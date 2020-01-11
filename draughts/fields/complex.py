import string
import random

from .bases import ProxyField, Field, MultivaluedField


class Compound(ProxyField):
    """A field who's type is defined by another model object."""
    def __init__(self, model, **kwargs):
        super().__init__(**kwargs)
        self.model = model

    def cast(self, value):
        if isinstance(value, self.model):
            return value, value._data
        obj = self.model(value)
        return obj, obj._data

    def sample(self):
        from ..randomizer import sample
        return sample(self.model)

    def flat_fields(self, prefix):
        from ..model_decorator import model_fields_flat
        return {prefix + '.' + _n: _v for _n, _v in model_fields_flat(self.model).items()}


class DelayedCompound(ProxyField):
    """A field who's type is defined by another model object.

    This variant of compound can be used in cases where the
    """
    # def __init__(self, model, **kwargs):
    #     super().__init__(**kwargs)
    #     self.model = model
    #
    # def cast(self, value):
    #     if isinstance(value, self.model):
    #         return value, value._data
    #     obj = self.model(value)
    #     return obj, obj._data
    #
    # def sample(self):
    #     from ..randomizer import sample
    #     return sample(self.model)
    #
    # def flat_fields(self, prefix):
    #     from ..model_decorator import model_fields_flat
    #     return {prefix + '.' + _n: _v for _n, _v in model_fields_flat(self.model).items()}


class List(ProxyField):
    def __init__(self, field: Field, **kwargs):
        super().__init__(**kwargs)
        assert isinstance(field, (MultivaluedField, ProxyField))
        self.field = field
        self.proxy = _list_proxy(field.cast)

    def cast(self, value):
        # Only cast to list when we must to preserve structure of source document
        if not isinstance(value, list):
            value = list(value)
        if isinstance(value, self.proxy):
            return value, value._data
        obj = self.proxy(value)
        return obj, obj._data

    def sample(self):
        return self.proxy([self.field.sample() for _ in range(random.randint(0, 10))])

    def flat_fields(self, prefix):
        return self.field.flat_fields(prefix + '[].')


def _list_proxy(cast):
    class ListProxy:
        __slots__ = ['_data', '_view']

        """A proxy object over a list to enforce typing."""

        def __init__(self, data):
            self._view = []
            self._data = data
            for index, _d in enumerate(data):
                _v, self._data[index] = cast(_d)
                self._view.append(_v)

        def append(self, item):
            view, data = cast(item)
            self._view.append(view)
            self._data.append(data)

        def extend(self, iterable):
            _t = [cast(_o) for _o in iterable]
            self._view.extend((_r[0] for _r in _t))
            self._data.extend((_r[1] for _r in _t))

        def insert(self, index, item):
            v, d = cast(item)
            self._view.insert(index, v)
            self._data.insert(index, d)

        def __len__(self):
            return len(self._data)

        def __setitem__(self, key, value):
            if isinstance(key, slice):
                view = [cast(_o) for _o in value]
                self._view[key] = [_v[0] for _v in view]
                self._data[key] = [_v[1] for _v in view]
            else:
                view, data = cast(value)
                self._view[key] = view
                self._data[key] = data

        def __iadd__(self, other):
            self.extend(other)
            return self

        def __getitem__(self, item):
            return self._view[item]

        def __eq__(self, other):
            return self._data == other._data

    return ListProxy


class Mapping(ProxyField):
    def __init__(self, field: ProxyField, **kwargs):
        super().__init__(**kwargs)
        self.field = field
        self.proxy = _mapping_proxy(field)

    def cast(self, value):
        if not isinstance(value, dict):
            value = dict(value)
        if isinstance(value, self.proxy):
            return value, value._data
        obj = self.proxy(value)
        return obj, obj._data

    def sample(self):
        return self.proxy({
            ''.join(random.choices(string.ascii_letters, k=10)): self.field.sample()
            for _ in range(random.randint(0, 10))
        })

    def flat_fields(self, prefix):
        return self.field.flat_fields(prefix + '.*.')


def _mapping_proxy(child: Field):
    cast = child.cast

    class MappingProxy:
        """A proxy object over a list to enforce typing."""
        __slots__ = ['_data', '_view']

        def __init__(self, data):
            self._view = {}
            self._data = data
            for _k, _o in data.items():
                self._view[_k], self._data[_k] = cast(_o)

        def __iter__(self):
            return iter(self._view)

        def __setitem__(self, key, value):
            view, data = cast(value)
            self._view[key] = view
            self._data[key] = data

        def __contains__(self, item):
            return item in self._view

        def __getitem__(self, item):
            return self._view[item]

        def __len__(self):
            return len(self._data)

        def __eq__(self, other):
            return self._data == other._data

        def values(self):
            return self._view.values()

        def keys(self):
            return self._data.keys()

        def items(self):
            return self._view.items()

    return MappingProxy
