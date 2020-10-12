import enum
import typing
import time

import pytest
import json

from draughts import model, model_fields, model_fields_flat, raw, dumps
from draughts.fields import String, Integer, List, Compound, Mapping, Timestamp, Enum, Keyword, Bytes, Boolean, UUID


class CatError(Exception):
    """A unique exception class."""
    pass


def test_index_defaults():
    @model
    class Test1:
        default = String()
        indexed = String(index=True)
        not_indexed = String(index=False)

    fields = model_fields(Test1)
    assert fields['default']['index'] is None
    assert fields['indexed']['index'] is True
    assert fields['not_indexed']['index'] is False

    @model(index=True)
    class Test2:
        default = String()
        indexed = String(index=True)
        not_indexed = String(index=False)

    fields = model_fields(Test2)
    assert fields['default']['index'] is True
    assert fields['indexed']['index'] is True
    assert fields['not_indexed']['index'] is False

    @model(index=False)
    class Test3:
        default = String()
        indexed = String(index=True)
        not_indexed = String(index=False)

    fields = model_fields(Test3)
    assert fields['default']['index'] is False
    assert fields['indexed']['index'] is True
    assert fields['not_indexed']['index'] is False


@model
class Label:
    first = String()
    second = Integer()


def test_creation(subtests):

    data_1 = dict(first='abc', second=567)
    from_dict = Label(data_1)

    from_args = Label(first='abc', second=567)
    data_2 = raw(from_args)

    for name, instance, data in [('from_dict', from_dict, data_1), ('from_args', from_args, data_2)]:
        with subtests.test(msg=name):
            assert raw(instance) == data

            assert instance.first == 'abc'
            assert instance.second == 567
            assert data['first'] == 'abc'
            assert data['second'] == 567

            instance.first = 'xyz'
            instance.second = 123

            assert instance.first == 'xyz'
            assert instance.second == 123
            assert data['first'] == 'xyz'
            assert data['second'] == 123


def test_extra_arguments():
    with pytest.raises(ValueError):
        Label(first='abc', second=123, third='red')

    with pytest.raises(ValueError):
        Label(dict(first='abc', second=123, third='red'))


def test_type_validation():
    with pytest.raises(ValueError):
        Label(dict(cats=123))

    instance = Label(first='abc', second=567)

    with pytest.raises(ValueError):
        instance.second = 'cats'


def test_properties():
    @model
    class Test:
        value = String()

        @property
        def first(self):
            return self.value

        @first.setter
        def first(self, value):
            value = str(value)
            if value.startswith('cat'):
                raise CatError()
            self.value = value

    instance = Test(value='abc')
    assert instance.first == 'abc'

    instance.first = 'xyz'
    assert instance.first == 'xyz'

    instance.first = 123
    assert instance.first == '123'

    with pytest.raises(CatError):
        instance.first = 'cats'


def test_setters_side_effects():
    """Test setters that change other field values."""

    # noinspection PyPropertyAccess, PyPropertyDefinition
    @model
    class Test:
        _a = Integer()
        _b = Integer()
        best = Integer()

        @property
        def a(self):
            return self._a

        @a.setter
        def a(self, value):
            self._a = value
            self.best = min(self.b, self.a)

        @property
        def b(self):
            return self._b

        @b.setter
        def b(self, value):
            self._b = value
            self.best = min(self.a, self.b)

    instance = Test(dict(_a=-100, _b=10, best=-100))

    instance.a = 50
    assert instance.best == 10
    instance.b = -10
    assert instance.best == -10


# noinspection PyPropertyAccess
def test_getters():
    # noinspection PyPropertyDefinition
    @model
    class Test:
        first: int = Integer()

        @property
        def second(self):
            return self.first if self.first >= 1 else 100

    instance = Test(dict(first=10))
    assert instance.second == 10

    instance.first = -1
    assert instance.second == 100

    instance.first = 500
    assert instance.second == 500


def test_create_compound():
    @model
    class TestCompound:
        key = String()
        value = String()

    @model
    class Test:
        first = Compound(TestCompound)

    test = Test({'first': {'key': 'a', 'value': 'b'}})
    assert test.first.key == 'a'
    test.first.key = 100
    assert test.first.key == '100'

    assert raw(test) == {
        'first': {
            'key': '100',
            'value': 'b'
        }
    }

    assert test == {
        'first': {
            'key': '100',
            'value': b'b'
        }
    }

    assert dumps(test) == json.dumps({
        'first': {
            'key': '100',
            'value': 'b'
        }
    })


def test_methods():
    @model
    class HasMethod:
        a = Integer()

        def return_a(self):
            return self.a

    x = HasMethod(a=100)
    assert x.return_a() == 100


def test_class_methods():
    @model
    class HasStatic:
        a = Integer()

        @classmethod
        def return_model_name(cls):
            return cls.__name__

    assert HasStatic.return_model_name() == 'HasStatic'


def test_static_methods():
    @model
    class HasStatic:
        a = Integer()

        @staticmethod
        def return_noun():
            return 'frog'

    assert HasStatic.return_noun() == 'frog'


def test_static_attribute():
    @model
    class HasStaticData:
        b = 999
        a = Integer()

        @classmethod
        def get_b(cls):
            return cls.b

    x = HasStaticData(a=100)
    assert x.b == 999
    assert HasStaticData.b == 999
    assert x.get_b() == 999
    assert HasStaticData.get_b() == 999
    HasStaticData.b = 9
    assert x.b == 9
    assert HasStaticData.b == 9
    assert x.get_b() == 9
    assert HasStaticData.get_b() == 9


def test_json():
    @model
    class Inner:
        number = Integer()
        value = String()

    @model
    class Test:
        a: Inner = Compound(Inner)
        b = Integer()

    a = Test(dict(b=10, a={'number': 499, 'value': 'cats'}))
    b = Test(json.loads(dumps(a)))

    assert b.b == 10
    assert b.a.number == 499
    assert b.a.value == 'cats'


def test_create_list():
    @model
    class Test:
        values: typing.List[int] = List(Integer())

    _ = Test(dict(values=[]))
    test = Test(dict(values=[0, 100]))

    with pytest.raises(ValueError):
        Test(dict(values=['bugs']))

    with pytest.raises(ValueError):
        Test(dict(values='bugs'))

    assert test.values[0] == 0
    assert test.values[1] == 100

    test.values = [0, 100, 5]
    test.values.pop()

    with pytest.raises(ValueError):
        test.values = ['red']

    test.values.append(10)
    assert len(test.values) == 3

    with pytest.raises(ValueError):
        test.values.append('cats')

    with pytest.raises(ValueError):
        test.values[0] = 'cats'

    test.values += range(5)
    assert len(test.values) == 8

    test.values.extend(range(2))
    assert len(test.values) == 10

    test.values.insert(0, -100)
    assert len(test.values) == 11
    assert test.values[0] == -100

    test.values[0:5] = range(5)
    assert len(test.values) == 11
    for ii in range(5):
        assert test.values[ii] == ii

    with pytest.raises(ValueError):
        test.values[0:2] = ['cats', 0]


def test_list_of_lists():

    @model
    class Test:
        data = List(List(Integer()))

    x = Test(data=[[1, 2, 3], [4, 5, 6]])
    assert x.data[0][1] == 2
    x.data[0][0] = 100

    with pytest.raises(ValueError):
        x.data[0][0] = 'dag'


def test_create_list_compounds():
    @model
    class Entry:
        value = Integer()
        key = String()

    @model
    class Test:
        values: typing.List[Entry] = List(Compound(Entry))

    fields = model_fields(Test)
    assert len(fields) == 1
    fields = model_fields_flat(Test)
    assert len(fields) == 2

    _ = Test(dict(values=[]))
    test = Test({'values': [
        {'key': 'cat', 'value': 0},
        {'key': 'rat', 'value': 100}
    ]})

    with pytest.raises(ValueError):
        Test(values=['bugs'])

    with pytest.raises(ValueError):
        Test(values='bugs')

    assert test.values[0].value == 0
    assert test.values[1].value == 100

    test.values.append({'key': 'bat', 'value': 50})

    assert len(test.values) == 3

    with pytest.raises(ValueError):
        test.values.append(1000)

    with pytest.raises(ValueError):
        test.values[0] = 'cats'

    with pytest.raises(ValueError):
        test.values[0] = {'key': 'bat', 'value': 50, 'extra': 1000}

    test.values[0].key = 'dog'

    test.values.append(Entry(key='zoo', value=99))


def test_defaults():

    @model
    class InnerA:
        number = Integer(default=10)
        value = String()

    @model
    class InnerB:
        number = Integer()
        value = String()

    @model
    class Test:
        a: InnerA = Compound(InnerA)
        b: InnerB = Compound(InnerB)
        c: InnerB = Compound(InnerB, default={'number': 99, 'value': 'yellow'})
        x = Integer()
        y = Integer(default=-1)

    # Build a model with missing data found in the defaults
    test = Test({
        'a': {'value': 'red'},
        'b': {'number': -100, 'value': 'blue'},
        'x': -55
    })

    assert test.a.number == 10
    assert test.a.value == 'red'
    assert test.b.number == -100
    assert test.b.value == 'blue'
    assert test.c.number == 99
    assert test.c.value == 'yellow'
    assert test.x == -55
    assert test.y == -1


def test_mapping():
    @model
    class Test:
        a = Mapping(Integer(), default={})

    test = Test({})

    assert len(test.a) == 0

    with pytest.raises(KeyError):
        _ = test.a['abc']

    test.a['cat'] = 10
    test.a['dog'] = -100

    assert len(test.a) == 2
    assert test.a['dog'] == -100

    with pytest.raises(ValueError):
        test.a['red'] = 'can'

    test = Test({'a': {'walk': 100}})
    assert len(test.a) == 1
    assert test.a['walk'] == 100


def test_mapping_of_mapping():
    @model
    class Test:
        a = Mapping(Mapping(Integer()), default={})

    test = Test({'a': {'x': {}}})

    assert len(test.a) == 1

    with pytest.raises(KeyError):
        _ = test.a['abc']

    _ = test.a['x']
    with pytest.raises(KeyError):
        _ = test.a['x']['abc']

    with pytest.raises(TypeError):
        test.a['cat'] = 10

    test.a['x']['cat'] = 10
    test.a['y'] = {'dog': -100}

    assert len(test.a) == 2
    assert len(test.a['x']) == 1
    assert len(test.a['y']) == 1
    assert test.a['y']['dog'] == -100

    with pytest.raises(ValueError):
        test.a['red'] = 'can'
    with pytest.raises(ValueError):
        test.a['y']['red'] = 'can'

    test = Test({'a': {'b': {'walk': 100}}})
    assert len(test.a) == 1
    assert len(test.a['b']) == 1
    assert test.a['b']['walk'] == 100


def test_mapping_of_compound():
    @model
    class Pair:
        a = Integer()
        b = Integer()

    @model
    class Test:
        a = Mapping(Compound(Pair), factory=dict)

    test = Test({})

    assert len(test.a) == 0

    with pytest.raises(KeyError):
        _ = test.a['abc']

    test.a['cat'] = {'a': 10, 'b': -100}
    test.a['dog'] = Pair(a=-100, b=999)

    assert len(test.a) == 2
    assert test.a['dog'].a == -100

    with pytest.raises(ValueError):
        test.a['red'] = 'can'

    test = Test({'a': {'walk': dict(a=1, b=1)}})
    assert len(test.a) == 1
    assert test.a['walk'].a == 1
    assert test.a['walk'].b == 1


def test_enum():
    class LoggingTargets(enum.Enum):
        Magic = 0
        Solr = 1
        ElasticSearch = 2

    @model
    class EnumTest:
        enum = Enum(LoggingTargets)

    et = EnumTest({"enum": LoggingTargets.Magic})
    assert et.enum == LoggingTargets.Magic

    et.enum = LoggingTargets.Magic
    assert et.enum == LoggingTargets.Magic
    et.enum = LoggingTargets.Solr
    assert et.enum == LoggingTargets.Solr
    et.enum = LoggingTargets.ElasticSearch
    assert et.enum == LoggingTargets.ElasticSearch

    et.enum = 0
    assert et.enum == LoggingTargets.Magic
    et.enum = 1
    assert et.enum == LoggingTargets.Solr
    et.enum = 2
    assert et.enum == LoggingTargets.ElasticSearch

    et.enum = "Magic"
    assert et.enum == LoggingTargets.Magic
    et.enum = "Solr"
    assert et.enum == LoggingTargets.Solr
    et.enum = "ElasticSearch"
    assert et.enum == LoggingTargets.ElasticSearch

    with pytest.raises(ValueError):
        et.enum = "bob"

    with pytest.raises(ValueError):
        et.enum = "mysql"

    with pytest.raises(ValueError):
        et.enum = ["a"]


def test_timestamp():
    @model
    class Test:
        start: float = Timestamp()
        end: float = Timestamp(factory=time.time)

    a = Test(start=0)
    assert a.start == 0
    a.start = time.time()

    assert a.start - a.end < 1

    with pytest.raises(ValueError):
        a.end = 'now'


# def test_dates():
#     @model
#     class Test:
#         start: float = DateTime()
#         end: float = DateTime(factory=time.time)
#
#     a = Test(start=0)
#     assert a.start == 0
#     a.start = time.time()
#
#     assert a.start - a.end < 1
#
#     with pytest.raises(ValueError):
#         a.end = 'now'


def test_optional():
    @model
    class Pair:
        a = Integer()
        b = Integer()

    @model
    class Test:
        a = Integer(optional=True)
        b = List(Integer(), optional=True)
        c = Compound(Pair, optional=True)
        d = Mapping(Compound(Pair), optional=True)

    x = Test(b=None)

    assert x.a is None
    x.a = 10
    with pytest.raises(ValueError):
        x.a = 'now'
    assert x.a == 10
    x.a = None
    assert x.a is None

    x.b = [10, '100']
    assert x.b == [10, 100]

    x.c = dict(a=999, b=999)
    assert x.c.a == 999

    x.d = dict(aaa=dict(a=-999, b=999))
    assert x.d['aaa'].a == -999


def test_optional_compound():
    """Ensure that optional compounds are still handled as normal."""
    @model
    class Inner:
        label = Keyword()
        count = Integer()

    @model
    class Outer:
        tag = Compound(Inner, optional=True)

    tag_data = {'label': 'label', 'count': 10}
    x = Outer(tag=tag_data)
    assert x.tag.label == 'label'
    x.tag.label = 'big'
    assert tag_data['label'] == 'big'

    assert raw(x) == {'tag': tag_data}


# TODO maybe tagged unions?
# def test_union():
#     raise NotImplementedError()

def test_detect_missing_fields():
    @model
    class Outer:
        tag = Compound(Label)

    with pytest.raises(ValueError):
        Outer()

    with pytest.raises(ValueError):
        Label()


def test_bytes_field():
    @model
    class Test:
        data = Bytes()

    assert Test(data='str').data == b'str'


def test_boolean_field():
    @model
    class Test:
        data = Boolean()

    assert Test(data='').data is False
    assert Test(data='false').data is False
    assert Test(data=0).data is False
    assert Test(data=False).data is False
    assert Test(data=[]).data is False
    assert Test(data='FalSe').data is False
    assert Test(data=None).data is False

    assert Test(data=True).data is True
    assert Test(data='true').data is True

    with pytest.raises(ValueError):
        Test()


def test_uuid_field():
    @model
    class Test:
        data = UUID()
        rand: str = UUID(factory='random')

    x = Test(data='an-id-string')
    assert x.data == 'an-id-string'
    assert len(x.rand) == 32
