import fractions
import json
import uuid
import random
import string
from typing import Sequence

import arrow

from .bases import Field, MultiField

class Any(Field):
    def cast(self, value):
        return value

    def sample(self):
        return 4


class Boolean(Field):
    def cast(self, value):
        if isinstance(value, str):
            if value[0:5].lower() == 'false':
                return False
        return bool(value)

    def sample(self):
        return random.getrandbits(1) == 0


class Integer(Field):
    def cast(self, value):
        return int(value)

    def sample(self):
        return random.randint(-2**30, 2**30)


class Float(Field):
    def cast(self, value):
        return float(value)

    def sample(self):
        return random.random() * 1000 - 500


class SeparatedFraction(MultiField):
    """Store a fraction as two values.

    Most
    """
    def cast(self, value) -> Sequence:
        if isinstance(value, fractions.Fraction):
            pass
        elif isinstance(value, (tuple, list)):
            value = fractions.Fraction(*value)
        else:
            value = fractions.Fraction(value)
        return value.numerator, value.denominator

    def proxy(self, parent, values):
        fraction = fractions.Fraction(*values)
        parent[self.name + '_numerator'] = fraction.numerator
        parent[self.name + '_denominator'] = fraction.denominator
        return fraction

    def sample(self):
        return fractions.Fraction(random.randint(-1000000, 100000), random.randint(0, 100000))

    def components(self):
        return (
            self.name + '_numerator',
            self.name + '_denominator'
        )


class String(Field):
    def cast(self, value):
        if isinstance(value, bytes):
            return value.decode()
        return str(value)

    def sample(self):
        length = random.randint(0, 128)
        return ''.join(random.choices(string.ascii_letters + string.digits + string.whitespace, k=length))


class Bytes(Field):
    def cast(self, value):
        if isinstance(value, str):
            return value.encode()
        return bytes(value)

    def sample(self):
        length = random.randint(0, 2**18)
        return bytes(random.getrandbits(8) for _ in range(length))


class Keyword(String):
    """A short string with symbolic value."""
    def sample(self):
        length = random.randint(0, 128)
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


class UUID(Keyword):
    def __init__(self, **kwargs):
        if kwargs.get('factory') == 'random':
            kwargs['factory'] = lambda: uuid.uuid4().hex
        super().__init__(**kwargs)


class Text(String):
    """A string with natural content."""
    def sample(self):
        chunks = random.randint(0, 128)
        return '\n'.join(super(Text, self).sample() for _ in range(chunks))


class Timestamp(Float):
    """A floating point number representing an offset from epoch"""
    pass


class DateString(String):
    """A field storing date."""
    def cast(self, value):
        if value == "NOW":
            value = arrow.utcnow().isoformat()

        try:
            return arrow.Arrow.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ", 'utc').isoformat()
        except (TypeError, ValueError):
            return arrow.get(value).isoformat()

    def sample(self):
        return '2020-03-20T14:28:23.382748'


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

    def sample(self):
        return random.choice(list(self.conversion.values()))

    def cast(self, value):
        try:
            return self.conversion[value]
        except (KeyError, TypeError):
            raise ValueError(f"Not an accepted enum value {value}")


class JSON(String):
    """A string field that checks that its content is always valid JSON"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def cast(self, value):
        value = super().cast(value)
        json.loads(value)
        return value

    def sample(self):
        return random.choice([
            '{}',
            '[]',
            '0',
            '"abc"',
            'null',
        ])
