import json

from .model_decorator import model, dumps, raw
from . import fields
from .randomizer import minimal_sample, sample


@model
class ManyTypes:
    integer = fields.Integer()
    float = fields.Float()


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
