""""""
import inspect
import json
import types


class Field:
    """An abstract data field for a model."""
    def __init__(self, **kwargs):
        self.metadata = kwargs
        self.metadata_defaults = {}
        self.name = None

    def __getitem__(self, item):
        return self.metadata.get(item, self.metadata_defaults.get(item))

    def cast(self, value):
        raise NotImplementedError()

    def dump(self, value):
        return value


class Integer(Field):
    def cast(self, value):
        return int(value)


class Float(Field):
    def cast(self, value):
        return int(value)


class String(Field):
    def cast(self, value):
        return str(value)


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
            proxy = self.__existing_list_proxies[child] = _typedList(child)
        return proxy


def _typedList(child):
    cast = child.cast

    class TypedList(list):
        def __init__(self, data):
            super().__init__(cast(o) for o in data)

        def append(self, object):
            super().append(cast(object))

        def extend(self, iterable):
            super().extend((cast(o) for o in iterable))

        def __setitem__(self, key, value):
            if isinstance(key, slice):
                return super().__setitem__(key, (cast(o) for o in value))
            return super().__setitem__(key, cast(value))

    return TypedList


class Compound(Field):
    """A field who's type is defined by another model object."""
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self.model = model

    def cast(self, value):
        if isinstance(value, self.model):
            return value
        return self.model(value)

    def dump(self, value):
        return value.to_dict()

    def flat_fields(self):
        return self.model.flat_fields()


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
    casts = {}        # Each field's cast function
    properties = {}   # Any previously defined properties
    methods = {}      # Any methods from the class we want to preserve
    for name, field in cls.__dict__.items():
        if isinstance(field, Field):
            casts[name] = field.cast
            fields[name] = field
            field.name = name
            field.metadata_defaults = metadata

            if isinstance(field, (Compound, List)):
                for sub_name, sub_field in field.flat_fields().items():
                    flat_fields[name + '.' + sub_name] = sub_field
            else:
                flat_fields[name] = field

        elif isinstance(field, property):
            properties[name] = field

        elif callable(field) or isinstance(field, (classmethod, staticmethod)):
            methods[name] = field

    field_keys = list(fields.keys())
    fields_items = list(fields.items())

    class ModelClass:
        __slots__ = field_keys

        def __init__(self, *args, **kwargs):
            data = args[0] if args else {}

            if not isinstance(data, dict):
                raise ValueError("Unexpected parameter type for model construction")

            kw_pop = kwargs.pop
            data_pop = data.pop

            for name, field in fields_items:
                cast = casts[name]
                if name in kwargs:
                    object_setattr(self, name, cast(kw_pop(name)))
                elif name in data:
                    object_setattr(self, name, cast(data_pop(name)))
                elif 'default' in field.metadata:
                    object_setattr(self, name, cast(field['default']))
                else:
                    raise ValueError(f"Missing key [{name}] to construct {cls.__name__}")

            if data:
                raise ValueError(f"Unexpected key provided: {data.keys()}")

            if kwargs:
                raise ValueError(f"Unexpected key provided: {kwargs.keys()}")

        def to_dict(self):
            return {
                name: fields[name].dump(getattr(self, name))
                for name, field in fields.items()
            }

        def to_json(self):
            return json.dumps(self.to_dict())

        def __setattr__(self, key, value):
            try:
                object_setattr(self, key, casts[key](value))
            except AttributeError:
                super().__setattr__(key, value)

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

        @staticmethod
        def fields():
            return fields

        @staticmethod
        def flat_fields():
            return flat_fields

    # Lets over write some class properties to make it a little nicer
    ModelClass.__name__ = cls.__name__
    ModelClass.__doc__ = cls.__doc__

    # # Apply the properties to the class so that our attribute access works
    # for name, field in compounds.items():
    #     setattr(ModelClass, name, CompoundProperty(name, field))
    # for name, field in lists.items():
    #     setattr(ModelClass, name, ListProperty(name, field))
    # for name, field in basic.items():
    #     setattr(ModelClass, name, fieldProperty(name, field.cast))
    #
    # If there were any pre-defined properties on the class make sure it is put back
    for name, _p in properties.items():
        setattr(ModelClass, name, _p)
    for name, _p in methods.items():
        setattr(ModelClass, name, _p)

    return ModelClass
