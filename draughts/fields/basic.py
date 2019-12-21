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
        return int(value)


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
