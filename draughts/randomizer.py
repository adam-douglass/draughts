from .model_decorator import model_fields
from .fields.bases import Field, ProxyField, MultivaluedField
from . import fields


def minimal_field_sample(field_spec: Field):
    if isinstance(field_spec, (ProxyField, MultivaluedField)):
        # Explicitly recursively call minimal sample on compounds
        if isinstance(field_spec, fields.Compound):
            return minimal_sample(field_spec.model)
        elif isinstance(field_spec, ProxyField):
            # ProxyField types should handle an empty iterable, but return a tuple
            return field_spec.cast([])[0]
        else:
            # MultiValueField types should be able to handle an empty iterable
            return field_spec.cast([])
    # all non complex fields can be sampled directly in the minimal case
    return field_spec.sample()


def minimal_sample(model, **data):
    for field_name, field_spec in model_fields(model).items():
        if field_spec['optional'] or field_name in data:
            continue
        if 'default' not in field_spec and 'factory' not in field_spec:
            data[field_name] = minimal_field_sample(field_spec)
    return model(data)


def sample(model, **data):
    for field_name, field_spec in model_fields(model).items():
        if field_name in data:
            continue
        data[field_name] = field_spec.sample()
    return model(data)
