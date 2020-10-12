""""""
import json
import weakref

import typing
from typing import Dict

from .fields.bases import ProxyField, Field


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

            if field.metadata.get('optional', False):
                def make_optional_cast(_c):
                    def _cast(value):
                        if value is None:
                            return None
                        return _c(value)
                    return _cast
                field.cast = casts[_name] = make_optional_cast(field.cast)

            if isinstance(field, ProxyField):
                compounds[_name] = field
                for sub_name, sub_field in field.flat_fields(prefix=_name).items():
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

    def field_property(_name, _cast, optional):
        if optional:
            class FieldProperty:
                def __get__(self, instance, objtype):
                    return instance._data.get(_name)

                def __set__(self, instance, value):
                    instance._data[_name] = _cast(value)

        else:
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
            instance._compounds[self.name], instance._data[self.name] = casts[self.name](value)

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
                    _compounds[name], data[name] = field.cast(kw_pop(name))
                elif data.get(name) is not None:
                    _compounds[name], data[name] = field.cast(data[name])
                elif 'default' in field.metadata:
                    _compounds[name], data[name] = field.cast(field['default'])
                elif 'factory' in field.metadata:
                    _compounds[name], data[name] = field.cast(field['factory']())
                elif field.metadata.get('optional', False):
                    _compounds[name] = None
                    # data[name] = None
                    continue
                else:
                    raise ValueError(f"Missing key [{name}] to construct {cls.__name__}")

            for name, field in basic.items():
                cast = casts[name]
                if name in kwargs:
                    data[name] = cast(kw_pop(name))
                elif name in data:
                    data[name] = cast(data[name])
                elif 'default' in field.metadata:
                    data[name] = cast(field['default'])
                elif 'factory' in field.metadata:
                    data[name] = cast(field['factory']())
                elif field.metadata.get('optional', False):
                    pass
                    # data[name] = None
                else:
                    raise ValueError(f"Missing key [{name}] to construct {cls.__name__}")

            if kwargs:
                raise ValueError(f"Unexpected key provided: {kwargs.keys()}")

        def __eq__(self, other):
            if isinstance(other, dict):
                return self == self.__class__(**other)
            for name in fields.keys():
                if getattr(self, name) != getattr(other, name):
                    return False
            return True

    # Lets over write some class properties to make it a little nicer
    ModelClass.__name__ = cls.__name__
    ModelClass.__doc__ = cls.__doc__
    if hasattr(cls, '__annotations__'):
        ModelClass.__annotations__ = cls.__annotations__

    _fields[ModelClass] = fields
    _flat_fields[ModelClass] = flat_fields

    # Apply the properties to the class so that our attribute access works
    for _name, field in compounds.items():
        setattr(ModelClass, _name, CompoundProperty(_name, field))
    for _name, field in basic.items():
        setattr(ModelClass, _name, field_property(_name, field.cast, field['optional']))

    # If there were any pre-defined properties on the class make sure it is put back
    for _name, _p in properties.items():
        setattr(ModelClass, _name, _p)
    for _name, _p in methods.items():
        setattr(ModelClass, _name, _p)
    for _name, _p in static_values.items():
        setattr(ModelClass, _name, _p)

    return ModelClass
