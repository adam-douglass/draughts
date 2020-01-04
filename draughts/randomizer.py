from .model_decorator import model_fields
from .fields.bases import Field, ProxyField


def minimal_field_sample(field_spec: Field):
    if isinstance(field_spec, ProxyField):
        raise NotImplementedError()
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
