from .bases import Field


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
        return float(value)


class String(Field):
    def cast(self, value):
        if isinstance(value, bytes):
            return value.decode()
        return str(value)


class Keyword(String):
    """A short string with symbolic value."""
    pass


class Text(String):
    """A string with natural content."""
    pass


class Timestamp(Float):
    """A floating point number representing an offset from epoch"""
    pass


class Optional(Field):
    """Allow None values for the wrapped field type."""
    def __init__(self, field):
        super().__init__(default=None)
        self.field = field

    def cast(self, value):
        if value is None:
            return value
        return self.field.cast(value)


class Enum(Field):
    """A field for enum values."""
    def __init__(self, enum, **kwargs):
        super().__init__(**kwargs)
        self.enum = enum
        self.conversion = {}
        for val in self.enum:
            self.conversion[val.value] = val
            self.conversion[val.name] = val
            self.conversion[val] = val

    def cast(self, value):
        try:
            return self.conversion[value]
        except (KeyError, TypeError):
            raise ValueError(f"Not an accepted enum value {value}")
