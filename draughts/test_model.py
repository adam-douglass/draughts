import typing
import pytest
import json

from draughts import model, model_fields, model_fields_flat, raw, dumps
from draughts.fields import String, Integer, Compound, List


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

# TODO is this actually the desired behaviour? it could be quite complex.
# def test_compound_index_defaults():
#     @model
#     class SubModel:
#         default = String()
#         indexed = String(index=True)
#         not_indexed = String(index=False)
#
#     @model
#     class Test1:
#         default = Compound(SubModel)
#         indexed = Compound(SubModel, index=True)
#         not_indexed = Compound(SubModel, index=False)
#
#     fields = Test1.flat_fields()
#     assert fields['default.default']['index'] is None
#     assert fields['default.indexed']['index'] is True
#     assert fields['default.not_indexed']['index'] is False
#
#     assert fields['indexed.default']['index'] is None
#     assert fields['indexed.indexed']['index'] is True
#     assert fields['indexed.not_indexed']['index'] is False
#
#     assert fields['not_indexed.default']['index'] is None
#     assert fields['not_indexed.indexed']['index'] is True
#     assert fields['not_indexed.not_indexed']['index'] is False


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

    with pytest.raises(KeyError):
        test.a['abc.abc.abc'] = None

    with pytest.raises(KeyError):
        test.a['4abc.abc.abc'] = None

    test.a['cat'] = 10
    test.a['dog'] = -100

    assert len(test.a) == 2
    assert test.a['dog'] == -100

    with pytest.raises(ValueError):
        test.a['red'] = 'can'

    test = Test({'a': {'walk': 100}})
    assert len(test.a) == 1
    assert test.a['walk'] == 100


def test_enum():
    @model(index=True, store=True)
    class EnumTest:
        enum = Enum(values=("magic", "solr", "elasticsearch"))

    et = EnumTest({"enum": "magic"})
    assert et.enum == "magic"

    et.enum = "magic"
    assert et.enum == "magic"
    et.enum = "solr"
    assert et.enum == "solr"
    et.enum = "elasticsearch"
    assert et.enum == "elasticsearch"

    with pytest.raises(ValueError):
        et.enum = "bob"

    with pytest.raises(ValueError):
        et.enum = "mysql"

    with pytest.raises(ValueError):
        et.enum = 1

    with pytest.raises(TypeError):
        et.enum = ["a"]

    with pytest.raises(ValueError):
        et.enum = True


def test_named_item_access():
    @model
    class Inner:
        a: int = Integer()
        b: int = Integer()

    @model
    class Test:
        a: Inner = Compound(Inner)
        b: int = Integer()

    test = Test(dict(a=dict(a=10, b=100), b=99))

    assert test.a['a'] == 10
    assert test['a'].a == 10
    assert test.a.a == 10
    assert test['a']['a'] == 10
    test.a['a'] = 1
    assert test.a['a'] == 1
    assert test['a'].a == 1
    assert test.a.a == 1
    assert test['a']['a'] == 1
    test['a'].a = -1
    assert test.a['a'] == -1
    assert test['a'].a == -1
    assert test.a.a == -1
    assert test['a']['a'] == -1

    with pytest.raises(KeyError):
        _ = test['x']

    with pytest.raises(KeyError):
        test['x'] = 100

    assert raw(test['a']) == {'a': -1, 'b': 100}


def test_dates():
    raise NotImplementedError()


def test_optional():
    raise NotImplementedError()


def test_union():
    raise NotImplementedError()

