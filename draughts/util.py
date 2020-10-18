import typing
from .model_decorator import model_fields
from .fields import ListTypes, Compound
import collections.abc


def recursive_update(d: typing.Dict, u: typing.Mapping) -> typing.Union[typing.Dict, typing.Mapping]:
    if d is None:
        return u

    if u is None:
        return d

    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v

    return d


def _construct_field(field, value):
    if isinstance(field, ListTypes):
        clean, dropped = [], []
        for item in value:
            _c, _d = _construct_field(field.field, item)
            if _c is not None:
                clean.append(_c)
            if _d is not None:
                dropped.append(_d)
        return clean or None, dropped or None

    elif isinstance(field, Compound):
        _c, _d = construct_safe(field.model, value)
        try:
            if len(_d) == 0:
                _d = None
        except TypeError:
            pass
        return _c, _d
    else:
        try:
            return field.cast(value), None
        except (ValueError, TypeError) as _:
            return None, value


def construct_safe(mod, data) -> typing.Tuple[typing.Any, typing.Dict]:
    if not isinstance(data, dict):
        return None, data
    fields = model_fields(mod)
    clean = {}
    dropped = {}
    for key, value in data.items():
        if key not in fields:
            dropped[key] = value
            continue

        _c, _d = _construct_field(fields[key], value)

        if _c is not None:
            clean[key] = _c
        if _d is not None:
            dropped[key] = _d

    try:
        return mod(clean), dropped
    except ValueError as _:
        return None, recursive_update(dropped, clean)
