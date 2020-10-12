import json
import enum
from copy import deepcopy

from draughts.model_decorator import model, dumps, raw
from draughts import fields
from draughts.randomizer import minimal_sample, sample


class Colour(enum.IntEnum):
    Red = 0
    Green = 1
    Blue = 2


@model
class ManyTypes:
    """A model using a bunch of types."""
    any = fields.Any()
    boolean = fields.Boolean()
    integer = fields.Integer()
    float = fields.Float()
    string = fields.String()
    keyword = fields.Keyword()
    uuid = fields.UUID()
    text = fields.Text()
    enum = fields.Enum(Colour)
    json = fields.JSON()


@model
class UnsafeTypes:
    """A model using types that can't be serialized using the json module"""
    bytes = fields.Bytes()


@model
class MultiTypes:
    compound = fields.Compound(ManyTypes)
    simple_list = fields.List(fields.Integer())
    proxy_list = fields.List(fields.Compound(ManyTypes))
    simple_map = fields.Mapping(fields.Integer())
    proxy_map = fields.Mapping(fields.Compound(ManyTypes))


def test_minimal_simple_fields():
    obj = minimal_sample(ManyTypes)
    assert obj != minimal_sample(ManyTypes)
    assert obj == ManyTypes(json.loads(dumps(obj)))
    assert obj == minimal_sample(ManyTypes, **raw(obj))


def test_simple_fields():
    obj = sample(ManyTypes)
    assert obj != sample(ManyTypes)
    assert obj == ManyTypes(json.loads(dumps(obj)))
    assert obj == sample(ManyTypes, **raw(obj))


def test_minimal_non_json_fields():
    obj = minimal_sample(UnsafeTypes)
    assert obj != minimal_sample(UnsafeTypes)
    assert obj == UnsafeTypes(deepcopy(raw(obj)))
    assert obj == minimal_sample(UnsafeTypes, **raw(obj))


def test_non_json_fields():
    obj = sample(UnsafeTypes)
    assert obj != sample(UnsafeTypes)
    assert obj == UnsafeTypes(deepcopy(raw(obj)))
    assert obj == sample(UnsafeTypes, **raw(obj))


def test_minimal_compound_fields():
    obj = minimal_sample(MultiTypes)
    assert obj != minimal_sample(MultiTypes)
    assert obj == MultiTypes(json.loads(dumps(obj)))
    assert obj == minimal_sample(MultiTypes, **raw(obj))


def test_compound_fields():
    obj = sample(MultiTypes)
    assert obj != sample(MultiTypes)
    assert obj == MultiTypes(json.loads(dumps(obj)))
    assert obj == sample(MultiTypes, **raw(obj))


def test_xeger_defaults():
    patterned_fields = [
        fields.MD5,
        fields.SHA1,
        fields.SHA256,
        fields.SSDeepHash,
        fields.Domain,
        fields.Email,
        fields.IP,
        fields.PrivateIP,
        fields.PhoneNumber,
        fields.MACAddress,
        fields.URI
    ]

    for field in patterned_fields:
        instance = field()
        assert instance.cast(instance.sample())