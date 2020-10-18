from draughts.util import construct_safe
from draughts import model, raw
from draughts.fields import Integer, List, Compound


@model
class Row:
    count = Integer()
    size = Integer()


@model
class Block:
    sections = List(Compound(Row))


def test_construct_safe():
    clean, dropped = construct_safe(Block, {
        'sections': [
            {'radish': 100, 'size': 10},
            {'count': 1, 'size': 1},
            {'count': 'QQ', 'size': 1},
            {'count': 10, 'size': -1},
            {'count': 2, 'size': 'big'},
            {'count': 100, 'size': 1},
            {'count': 3, 'siize': 1},
            'frogs',
            None,
        ]
    })

    assert raw(clean) == {
        'sections': [
            {'count': 1, 'size': 1},
            {'count': 10, 'size': -1},
            {'count': 100, 'size': 1},
        ]
    }