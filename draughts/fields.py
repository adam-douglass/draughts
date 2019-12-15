

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


class Any(Field):
    def cast(self, value):
        return value


class Boolean(Field):
    def cast(self, value):
        if isinstance(str, value):
            return value[0:4].lower() == 'true'
        return bool(value)


class Integer(Field):
    def cast(self, value):
        return int(value)


class Float(Field):
    def cast(self, value):
        return int(value)


class String(Field):
    def cast(self, value):
        if isinstance(bytes, value):
            return value.decode()
        return str(value)


class Timestamp(Float):
    pass


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
            return {self.name + '.' + n: k for n, k in model_fields_flat(self.field.model).items()}
        return {self.name or '': self.field}

    __existing_list_proxies = {}

    def build_proxy(self, child: Field):
        proxy = self.__existing_list_proxies.get(child)
        if not proxy:
            proxy = self.__existing_list_proxies[child] = _list_proxy(child)
        return proxy


def _list_proxy(child: Field):
    cast = child.cast

    if isinstance(child, (Compound, List)):
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
    else:
        # When we are dealing with non-compound types we don't need a separate
        # view, we can use the data directly
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


class Mapping(Field):
    def __init__(self, field: Field, **kwargs):
        super().__init__(**kwargs)
        self.field = field
        self.proxy = self.build_proxy(field)

    def cast(self, value):
        if isinstance(value, self.proxy):
            return value
        return self.proxy(value)

    __existing_proxies = {}

    def build_proxy(self, child: Field):
        proxy = self.__existing_proxies.get(child)
        if not proxy:
            proxy = self.__existing_proxies[child] = _mapping_proxy(child)
        return proxy


def _mapping_proxy(child: Field):
    cast = child.cast

    if isinstance(child, (Compound, List)):
        class MappingProxy:
            __slots__ = ['_data', '_view']

            """A proxy object over a list to enforce typing."""

            def __init__(self, data):
                self._data = data
                self._view = [cast(_o) for _o in data]

            def __setitem__(self, key, value):
                view = cast(value)
                self._view[key] = view
                self._data[key] = view._data

            def __getitem__(self, item):
                return self._view[item]
    else:
        # When we are dealing with non-compound types we don't need a separate
        # view, we can use the data directly
        class MappingProxy:
            __slots__ = ['_data']

            def __init__(self, data):
                self._data = data
                for index, row in enumerate(data):
                    data[index] = cast(row)

            def __len__(self):
                return len(self._data)

            def __setitem__(self, key, value):
                self._data[key] = cast(value)

            def __getitem__(self, item):
                return self._data[item]

    return MappingProxy


class Compound(Field):
    """A field who's type is defined by another model object."""
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self.model = model

    def cast(self, value):
        if isinstance(value, self.model):
            return value
        return self.model(value)
