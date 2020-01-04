import string
import random

from .bases import MultivaluedField, Field


class TypedList(list):
    def __init__(self, data, cast):
        self.__cast = cast
        super().__init__(cast(_r) for _r in data)

    def append(self, item):
        super().append(self.__cast(item))

    def extend(self, iterable):
        super().extend((self.__cast(_o) for _o in iterable))

    def insert(self, index, item):
        super().insert(index, self.__cast(item))

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            super().__setitem__(key, (self.__cast(_o) for _o in value))
        else:
            super().__setitem__(key, self.__cast(value))

    def __iadd__(self, other):
        super().extend((self.__cast(_o) for _o in other))
        return self


class SimpleList(MultivaluedField):
    """A list of non-complex """
    def __init__(self, field, **kwargs):
        super().__init__(**kwargs)
        self.field = field

    def cast(self, value):
        return TypedList(value, cast=self.field.cast)

    def sample(self):
        return TypedList([self.field.sample() for _ in range(random.randint(0, 10))], cast=self.field.cast)

    def flat_fields(self, prefix):
        return {prefix + '[]': self.field}


class TypedDict(dict):
    def __init__(self, data, cast):
        self.__cast = cast
        if isinstance(data, dict):
            super().__init__({k: cast(v) for k, v in data.items()})
        else:
            super().__init__({k: cast(v) for k, v in data})

    def setdefault(self, k, default=...):
        super().setdefault(k, default=self.__cast(default))

    def __setitem__(self, key, value):
        super().__setitem__(key, self.__cast(value))


class SimpleMapping(MultivaluedField):
    def __init__(self, field: Field, **kwargs):
        super().__init__(**kwargs)
        self.field = field

    def cast(self, value):
        return TypedDict(value, self.field.cast)

    def sample(self):
        return TypedDict({
            ''.join(random.choices(string.ascii_letters, k=10)): self.field.sample()
            for _ in range(random.randint(0, 10))
        }, self.field.cast)

    def flat_fields(self, prefix):
        return {prefix + '.*.': self.field}
