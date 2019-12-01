""""""
import inspect
import json
import types


class Field:
    __slots__ = ['metadata', 'metadata_defaults', 'name']

    """An abstract data field for a model."""
    def __init__(self, **kwargs):
        self.metadata = kwargs
        self.metadata_defaults = {}
        self.name = None

    def __getitem__(self, item):
        return self.metadata.get(item, self.metadata_defaults.get(item))

    def cast(self, value):
        raise NotImplementedError()


class Integer(Field):
    __slots__ = []

    def cast(self, value):
        return int(value)

    @staticmethod
    def assign(instance, name, value):
        object.__setattr__(instance, name, int(value))


class Float(Field):
    def cast(self, value):
        return int(value)


class String(Field):
    __slots__ = []

    def cast(self, value):
        return str(value)

    @staticmethod
    def assign(instance, name, value):
        object.__setattr__(instance, name, str(value))


class List(Field):
    def __init__(self, field: Field, **kwargs):
        super().__init__(**kwargs)
        self.field = field
        self.proxy = self.build_proxy(field)

    def cast(self, value):
        # Only cast to list when we must to preserve structure of source document
        if not isinstance(value, list):
            value = list(value)
        if isinstance(value, self.proxy):
            return value
        return self.proxy(value)

    def flat_fields(self):
        if isinstance(self.field, List):
            return {self.name + '.' + n: k for n, k in self.field.flat_fields().items()}
        elif isinstance(self.field, Compound):
            return {self.name + '.' + n: k for n, k in self.field.model.flat_fields().items()}
        return {self.name or '': self.field}

    __existing_list_proxies = {}

    def build_proxy(self, child: Field):
        proxy = self.__existing_list_proxies.get(child)
        if not proxy:
            proxy = self.__existing_list_proxies[child] = _listProxyFactory(child)
        return proxy


def _listProxyFactory(child: Field):
    if isinstance(child, (Compound, List)):
        cast = child.cast

        class ListProxy:
            __slots__ = ['_data', '_view']

            """A proxy object over a list to enforce typing."""

            def __init__(self, data):
                self._data = data
                self._view = [cast(_o) for _o in data]

            def append(self, item):
                view = cast(item)
                self._view.append(view)
                self._data.append(view._data)

            def extend(self, iterable):
                view = [cast(_o) for _o in iterable]
                self._view.extend(view)
                self._data.extend((_v._data for _v in view))

            def insert(self, index, item):
                self._data.insert(index, cast(item))

            def __len__(self):
                return len(self._data)

            def __setitem__(self, key, value):
                if isinstance(key, slice):
                    view = [cast(_o) for _o in value]
                    self._view[key] = view
                    self._data[key] = [_v._data for _v in view]
                else:
                    view = cast(value)
                    self._view[key] = view
                    self._data[key] = view._data

            def __iadd__(self, other):
                self.extend(other)
                return self

            def __getitem__(self, item):
                return self._view[item]

    elif isinstance(child, List):
        raise NotImplementedError()
    else:
        # When we are dealing with non-compound types we don't need a separate
        # view, we can use the data directly
        cast = child.cast

        class ListProxy:
            __slots__ = ['_data']

            def __init__(self, data):
                self._data = data
                for index, row in enumerate(data):
                    data[index] = cast(row)

            def append(self, item):
                self._data.append(cast(item))

            def extend(self, iterable):
                self._data.extend((cast(_o) for _o in iterable))

            def insert(self, index, item):
                self._data.insert(index, cast(item))

            def __len__(self):
                return len(self._data)

            def __setitem__(self, key, value):
                if isinstance(key, slice):
                    self._data[key] = (cast(_o) for _o in value)
                else:
                    self._data[key] = cast(value)

            def __iadd__(self, other):
                self._data.extend((cast(_o) for _o in other))
                return self

            def __getitem__(self, item):
                return self._data[item]

            def __getattr__(self, item):
                """If it isn't a method that adds to the the list just call it."""
                return getattr(self._data, item)

    return ListProxy


class Compound(Field):
    """A field who's type is defined by another model object."""
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self.model = model

    def cast(self, value):
        if isinstance(value, self.model):
            return value
        return self.model(value)


def model(cls=None, **metadata):
    object_setattr = object.__setattr__
    # If we are given default metadata
    if cls is None:
        def capture(cls):
            return model(cls, **metadata)
        return capture

    # Go through the class and pull out things we want
    fields = {}       # The fields of the object
    flat_fields = {}  # The fields of the object, recursively flattened
    compounds = {}    # Compound type fields
    lists = {}        # List field types
    basic = {}        # Fields with simple types only
    assign = {}
    casts = {}        # Each field's cast function
    properties = {}   # Any previously defined properties
    methods = {}      # Any methods from the class we want to preserve
    for name, field in cls.__dict__.items():
        if isinstance(field, Field):
            casts[name] = field.cast
            fields[name] = field
            field.name = name
            assign[name] = field.assign
            field.metadata_defaults = metadata
            if isinstance(field, Compound):
                compounds[name] = field
                for sub_name, sub_field in field.model.flat_fields().items():
                    flat_fields[name + '.' + sub_name] = sub_field
            elif isinstance(field, List):
                lists[name] = field
                for sub_name, sub_field in field.flat_fields().items():
                    flat_fields[sub_name] = sub_field
            else:
                basic[name] = field
                flat_fields[name] = field

        elif isinstance(field, property):
            properties[name] = field

        elif callable(field) or isinstance(field, (classmethod, staticmethod)):
            methods[name] = field

        # else:
        #     print(name, field)

    field_names = set(fields.keys())

    def fieldProperty(_name, _cast):
        class FieldProperty:
            # def __get__(self, instance, objtype):
            #     return getattr(instance, _name)

            def __set__(self, instance, value):
                instance._data[_name] = _cast(value)
        return FieldProperty()

    class CompoundProperty:
        def __init__(self, name, field):
            self.name = name
            self.field = field

        # def __get__(self, instance, objtype):
        #     return instance._compounds[self.name]

        def __set__(self, instance, value):
            value = instance._compounds[self.name] = casts[self.name](value)
            instance._data[self.name] = value._data

    class ListProperty:
        def __init__(self, name, field):
            self.name = name
            self.field = field

        # def __get__(self, instance, objtype):
        #     return instance._compounds[self.name]

        def __set__(self, instance, value):
            value = instance._compounds[self.name] = casts[self.name](value)
            instance._data[self.name] = value._data

    class ModelClass:
        __slots__ = ['_data'] + list(field_names)

        def __init__(self, *args, **kwargs):
            data = args[0] if args else {}
            object_setattr(self, '_data', data)

            if not isinstance(data, dict):
                raise ValueError("Unexpected parameter type for model construction")

            if set(data.keys()) - field_names:
                raise ValueError(f"Unexpected key provided: {set(data.keys()) - field_names}")

            for name, field in compounds.items():
                if name in kwargs:
                    view = field.model(kwargs.pop(name))
                elif name in data:
                    view = field.model(data[name])
                elif 'default' in field.metadata:
                    view = field.model(field['default'])
                else:
                    raise ValueError(f"Missing key [{name}] to construct {cls.__name__}")

                object_setattr(self, name, view)
                data[name] = view._data

            for name, field in lists.items():
                if name in kwargs:
                    view = field.proxy(kwargs.pop(name))
                elif name in data:
                    view = field.proxy(data[name])
                elif 'default' in field.metadata:
                    view = field.proxy(field['default'])
                else:
                    raise ValueError(f"Missing key [{name}] to construct {cls.__name__}")

                object_setattr(self, name, view)
                data[name] = view._data

            for name, field in basic.items():
                cast = casts[name]
                if name in kwargs:
                    data[name] = cast(kwargs.pop(name))
                elif name in data:
                    data[name] = cast(data[name])
                elif 'default' in field.metadata:
                    data[name] = cast(field['default'])
                else:
                    raise ValueError(f"Missing key [{name}] to construct {cls.__name__}")
                object_setattr(self, name, data[name])

            if kwargs:
                raise ValueError(f"Unexpected key provided: {kwargs.keys()}")

        def __setattr__(self, key, value):
            assign[key](self, key, value)

        def __getitem__(self, name):
            try:
                return getattr(self, name)
            except AttributeError:
                raise KeyError(name)

        def __setitem__(self, name, value):
            try:
                return setattr(self, name, value)
            except AttributeError:
                raise KeyError(name)

        def to_dict(self):
            return self._data

        def to_json(self):
            return json.dumps(self._data)

        @staticmethod
        def fields():
            return fields

        @staticmethod
        def flat_fields():
            return flat_fields

    # Lets over write some class properties to make it a little nicer
    ModelClass.__name__ = cls.__name__
    ModelClass.__doc__ = cls.__doc__

    # Apply the properties to the class so that our attribute access works
    # for name, field in compounds.items():
    #     setattr(ModelClass, name, CompoundProperty(name, field))
    # for name, field in lists.items():
    #     setattr(ModelClass, name, ListProperty(name, field))
    # for name, field in basic.items():
    #     setattr(ModelClass, name, fieldProperty(name, field.cast))

    # If there were any pre-defined properties on the class make sure it is put back
    for name, _p in properties.items():
        setattr(ModelClass, name, _p)
    for name, _p in methods.items():
        setattr(ModelClass, name, _p)

    return ModelClass
