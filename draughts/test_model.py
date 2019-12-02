import json
from typing import List
from tabulate import tabulate
import pytest

from draughts import model, struct_model, proxy_model, half_proxy


class CatError(Exception):
    """A unique exception class."""
    pass


@pytest.fixture(params=[model, struct_model, proxy_model], ids=['model', 'struct', 'proxy'])
def src(request):
    return request.param


def test_index_defaults(src):
    @src.model
    class Test1:
        default = src.String()
        indexed = src.String(index=True)
        not_indexed = src.String(index=False)

    fields = dict(Test1.fields())
    assert fields['default']['index'] is None
    assert fields['indexed']['index'] is True
    assert fields['not_indexed']['index'] is False

    @src.model(index=True)
    class Test2:
        default = src.String()
        indexed = src.String(index=True)
        not_indexed = src.String(index=False)

    fields = dict(Test2.fields())
    assert fields['default']['index'] is True
    assert fields['indexed']['index'] is True
    assert fields['not_indexed']['index'] is False

    @src.model(index=False)
    class Test3:
        default = src.String()
        indexed = src.String(index=True)
        not_indexed = src.String(index=False)

    fields = dict(Test3.fields())
    assert fields['default']['index'] is False
    assert fields['indexed']['index'] is True
    assert fields['not_indexed']['index'] is False


def test_compound_index_defaults(src):
    @src.model
    class SubModel:
        default = src.String()
        indexed = src.String(index=True)
        not_indexed = src.String(index=False)

    @src.model
    class Test1:
        default = src.Compound(SubModel)
        indexed = src.Compound(SubModel, index=True)
        not_indexed = src.Compound(SubModel, index=False)

    fields = Test1.flat_fields()
    assert fields['default.default']['index'] is None
    assert fields['default.indexed']['index'] is True
    assert fields['default.not_indexed']['index'] is False

    assert fields['indexed.default']['index'] is True
    assert fields['indexed.indexed']['index'] is True
    assert fields['indexed.not_indexed']['index'] is False

    assert fields['not_indexed.default']['index'] is False
    assert fields['not_indexed.indexed']['index'] is True
    assert fields['not_indexed.not_indexed']['index'] is False


def test_creation(src):
    @src.model
    class Test:
        first = src.String()
        second = src.Integer()

    instance = Test(dict(first='abc', second=567))

    assert instance.first == 'abc'
    assert instance.second == 567

    instance.first = 'xyz'
    instance.second = 123

    assert instance.first == 'xyz'
    assert instance.second == 123

    instance = Test(first='abc', second=567)

    assert instance.first == 'abc'
    assert instance.second == 567

    instance.first = 'xyz'
    instance.second = 123

    assert instance.first == 'xyz'
    assert instance.second == 123


def test_type_validation(src):
    @src.model
    class Test:
        first = src.String()
        second = src.Integer()

    with pytest.raises(ValueError):
        Test(dict(cats=123))

    instance = Test(first='abc', second=567)

    with pytest.raises(ValueError):
        instance.second = 'cats'


def test_properties(src):
    @src.model
    class Test:
        value = src.String()

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

# #
# # def test_setters_side_effects():
# #     """Test setters that change other field values."""
# #
# #     # noinspection PyPropertyAccess, PyPropertyDefinition
# #     @src.model
# #     class Test:
# #         _a = src.Integer()
# #         _b = src.Integer()
# #         best = src.Integer()
# #
# #         @a.setter
# #         def a(self, value):
# #             self.best = min(self.b, value)
# #             return value
# #
# #         @b.setter
# #         def b(self, value):
# #             self.best = min(self.a, value)
# #             return value
# #
# #     instance = Test(dict(a=-100, b=10, best=-100))
# #
# #     instance.a = 50
# #     assert instance.best == 10
# #     instance.b = -10
# #     assert instance.best == -10
#
# #
# # # noinspection PyPropertyAccess
# # def test_getters():
# #     # noinspection PyPropertyDefinition
# #     @src.model
# #     class Test(Model):
# #         first = src.Integer()
# #
# #         @first.getter
# #         def first(self, value):
# #             return value if value >= 1 else 100
# #
# #     instance = Test(dict(first=10))
# #     assert instance.first == 10
# #
# #     instance.first = -1
# #     assert instance.first == 100
# #
# #     instance.first = 500
# #     assert instance.first == 500
# #
#

def test_create_compound(src):
    @src.model
    class TestCompound:
        key = src.String()
        value = src.String()

    @src.model
    class Test:
        first = src.Compound(TestCompound)

    test = Test({'first': {'key': 'a', 'value': 'b'}})
    assert test.first.key == 'a'
    test.first.key = 100
    assert test.first.key == '100'

    assert test.to_dict() == {
        'first': {
            'key': '100',
            'value': 'b'
        }
    }

    assert test.to_json() == json.dumps({
        'first': {
            'key': '100',
            'value': 'b'
        }
    })


def test_methods(src):
    @src.model
    class HasMethod:
        a = src.Integer()

        def return_a(self):
            return self.a

    x = HasMethod(a=100)
    assert x.return_a() == 100


def test_class_methods(src):
    @src.model
    class HasStatic:
        a = src.Integer()

        @classmethod
        def return_model_name(cls):
            return cls.__name__

    assert HasStatic.return_model_name() == 'HasStatic'


def test_static_methods(src):
    @src.model
    class HasStatic:
        a = src.Integer()

        @staticmethod
        def return_noun():
            return 'frog'

    assert HasStatic.return_noun() == 'frog'


def test_static_attribute():
    @src.model
    class HasStaticData:
        b = 999
        a = src.Integer()

    x = HasStaticData(a=100)
    y = HasStaticData(a=100)
    assert x.b == 999
    y.b = 9
    assert x.b == 9



def test_json(src):
    @src.model
    class Inner:
        number = src.Integer()
        value = src.String()

    @src.model
    class Test:
        a: Inner = src.Compound(Inner)
        b = src.Integer()

    a = Test(dict(b=10, a={'number': 499, 'value': 'cats'}))
    b = Test(json.loads(a.to_json()))

    assert b.b == 10
    assert b.a.number == 499
    assert b.a.value == 'cats'


def test_create_list(src):
    @src.model
    class Test:
        values: List[int] = src.List(src.Integer())

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


def test_list_of_lists(src):

    @src.model
    class Test:
        data = src.List(src.List(src.Integer()))

    x = Test(data=[[1, 2, 3], [4, 5, 6]])
    assert x.data[0][1] == 2
    x.data[0][0] = 100

    with pytest.raises(ValueError):
        x.data[0][0] = 'dag'


def test_create_list_compounds(src):
    @src.model
    class Entry:
        value = src.Integer()
        key = src.String()

    @src.model
    class Test:
        values: List[Entry] = src.List(src.Compound(Entry))

    fields = Test.fields()
    assert len(fields) == 1
    fields = Test.flat_fields()
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


def test_defaults(src):

    @src.model
    class InnerA:
        number = src.Integer(default=10)
        value = src.String()

    @src.model
    class InnerB:
        number = src.Integer()
        value = src.String()

    @src.model
    class Test:
        a: InnerA = src.Compound(InnerA)
        b: InnerB = src.Compound(InnerB)
        c: InnerB = src.Compound(InnerB, default={'number': 99, 'value': 'yellow'})
        x = src.Integer()
        y = src.Integer(default=-1)

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

#
# def test_field_masking():
#     @src.model
#     class Test(Model):
#         a = src.Integer()
#         b = src.Integer()
#
#     test = Test(dict(a=10), mask=['a'])
#
#     assert test.a == 10
#
#     with pytest.raises(KeyMaskException):
#         _ = test.b
#
#     with pytest.raises(KeyMaskException):
#         test.b = 100
#
#
# def test_sub_field_masking():
#     @src.model
#     class Inner(Model):
#         a = src.Integer()
#         b = src.Integer()
#
#     @src.model
#     class Test(Model):
#         a = src.Compound(Inner)
#         b = src.Compound(Inner)
#
#     test = Test(dict(a=dict(a=10), b=dict(b=10)), mask=['a.a', 'b.b'])
#
#     assert test.a.a == 10
#
#     with pytest.raises(KeyMaskException):
#         _ = test.b.a
#
#     with pytest.raises(KeyMaskException):
#         test.a.b = 100


def test_mapping():
    @src.model
    class Test(Model):
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
    @src.model(index=True, store=True)
    class EnumTest(Model):
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


def test_named_item_access(src):
    @src.model
    class Inner:
        a = src.Integer()
        b = src.Integer()

    @src.model
    class Test:
        a = src.Compound(Inner)
        b = src.Integer()

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

    assert test['a'] == {'a': -1, 'b': 100}


def test_dates():
    raise NotImplementedError()


def test_optional():
    raise NotImplementedError()


def test_union():
    raise NotImplementedError()


