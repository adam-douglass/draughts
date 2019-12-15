""""""
import json
import weakref

import typing
from typing import Dict, TYPE_CHECKING

from .fields import Field, Compound, List


_fields: Dict[type, Dict[str, Field]] = typing.cast(Dict, weakref.WeakKeyDictionary())
_flat_fields: Dict[type, Dict[str, Field]] = typing.cast(Dict, weakref.WeakKeyDictionary())


def model_fields(cls: type):
    return _fields[cls]


def model_fields_flat(cls: type):
    return _flat_fields[cls]


def raw(obj):
    return getattr(obj, '_data')


def dumps(obj):
    return json.dumps(raw(obj))


def model(cls=None, **metadata):
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
    casts = {}        # Each field's cast function
    properties = {}   # Any previously defined properties
    methods = {}      # Any methods from the class we want to preserve
    static_values = {}

    for _name, field in cls.__dict__.items():
        if isinstance(field, Field):
            casts[_name] = field.cast
            fields[_name] = field
            field.name = _name
            field.metadata_defaults = metadata
            if isinstance(field, Compound):
                compounds[_name] = field
                for sub_name, sub_field in _flat_fields[field.model].items():
                    flat_fields[_name + '.' + sub_name] = sub_field
            elif isinstance(field, List):
                lists[_name] = field
                for sub_name, sub_field in field.flat_fields().items():
                    flat_fields[sub_name] = sub_field
            else:
                basic[_name] = field
                flat_fields[_name] = field

        elif isinstance(field, property):
            properties[_name] = field

        elif callable(field) or isinstance(field, (classmethod, staticmethod)):
            methods[_name] = field

        elif not _name.startswith('__') and not _name.endswith('__'):
            static_values[_name] = field

    field_names = set(fields.keys())

    def fieldProperty(_name, _cast):
        class FieldProperty:
            def __get__(self, instance, objtype):
                return instance._data[_name]

            def __set__(self, instance, value):
                instance._data[_name] = _cast(value)
        return FieldProperty()

    class CompoundProperty:
        def __init__(self, name, field):
            self.name = name
            self.field = field

        def __get__(self, instance, objtype):
            return instance._compounds[self.name]

        def __set__(self, instance, value):
            value = instance._compounds[self.name] = casts[self.name](value)
            instance._data[self.name] = value._data

    class ListProperty:
        def __init__(self, name, field):
            self.name = name
            self.field = field

        def __get__(self, instance, objtype):
            return instance._compounds[self.name]

        def __set__(self, instance, value):
            value = instance._compounds[self.name] = casts[self.name](value)
            instance._data[self.name] = value._data

    class ModelClass:
        __slots__ = ['_data', '_compounds']

        def __init__(self, *args, **kwargs):
            data = self._data = args[0] if args else {}
            _compounds = self._compounds = {}

            if not isinstance(data, dict):
                raise ValueError("Unexpected parameter type for model construction")

            kw_pop = kwargs.pop

            if set(data.keys()) - field_names:
                raise ValueError(f"Unexpected key provided: {set(data.keys()) - field_names}")

            for name, field in compounds.items():
                if name in kwargs:
                    _compounds[name] = field.model(kw_pop(name))
                elif name in data:
                    _compounds[name] = field.model(data[name])
                elif 'default' in field.metadata:
                    _compounds[name] = field.model(field['default'])
                elif 'factory' in field.metadata:
                    _compounds[name] = field.model(field['factory']())
                else:
                    raise ValueError(f"Missing key [{name}] to construct {cls.__name__}")

                data[name] = _compounds[name]._data

            for name, field in lists.items():
                if name in kwargs:
                    _compounds[name] = field.proxy(kw_pop(name))
                elif name in data:
                    _compounds[name] = field.proxy(data[name])
                elif 'default' in field.metadata:
                    _compounds[name] = field.proxy(field['default'])
                elif 'factory' in field.metadata:
                    _compounds[name] = field.model(field['factory']())
                else:
                    raise ValueError(f"Missing key [{name}] to construct {cls.__name__}")

                data[name] = _compounds[name]._data

            for name, field in basic.items():
                cast = casts[name]
                if name in kwargs:
                    data[name] = cast(kw_pop(name))
                elif name in data:
                    data[name] = cast(data[name])
                elif 'default' in field.metadata:
                    data[name] = cast(field['default'])
                elif 'factory' in field.metadata:
                    _compounds[name] = field.model(field['factory']())
                else:
                    raise ValueError(f"Missing key [{name}] to construct {cls.__name__}")

            if kwargs:
                raise ValueError(f"Unexpected key provided: {kwargs.keys()}")

        # def __getitem__(self, name):
        #     try:
        #         return getattr(self, name)
        #     except AttributeError:
        #         raise KeyError(name)
        #
        # def __setitem__(self, name, value):
        #     try:
        #         return setattr(self, name, value)
        #     except AttributeError:
        #         raise KeyError(name)

    # Lets over write some class properties to make it a little nicer
    ModelClass.__name__ = cls.__name__
    ModelClass.__doc__ = cls.__doc__
    ModelClass.__annotations__ = cls.__annotations__

    _fields[ModelClass] = fields
    _flat_fields[ModelClass] = flat_fields

    # Apply the properties to the class so that our attribute access works
    for _name, field in compounds.items():
        setattr(ModelClass, _name, CompoundProperty(_name, field))
    for _name, field in lists.items():
        setattr(ModelClass, _name, ListProperty(_name, field))
    for _name, field in basic.items():
        setattr(ModelClass, _name, fieldProperty(_name, field.cast))

    # If there were any pre-defined properties on the class make sure it is put back
    for _name, _p in properties.items():
        setattr(ModelClass, _name, _p)
    for _name, _p in methods.items():
        setattr(ModelClass, _name, _p)
    for _name, _p in static_values.items():
        setattr(ModelClass, _name, _p)

    return ModelClass
