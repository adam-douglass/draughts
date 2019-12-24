from .basic import Boolean, Integer, Float, Timestamp, Enum
from .basic import String, Keyword, Text, JSON, UUID
from .basic import Optional, Any
from .complex import Compound


def List(field_type, **kwargs):
    """A helper "class" to choose the right list class for a given field."""
    assert not isinstance(field_type, Optional)
    from .bases import MultivaluedField, ProxyField
    from .multivalued import SimpleList
    from .complex import List
    if isinstance(field_type, (MultivaluedField, ProxyField)):
        return List(field_type, **kwargs)
    return SimpleList(field_type, **kwargs)


def Mapping(field_type, **kwargs):
    """A helper "class" to choose the right list class for a given field."""
    assert not isinstance(field_type, Optional)
    from .bases import MultivaluedField, ProxyField
    from .multivalued import SimpleMapping
    from .complex import Mapping
    if isinstance(field_type, ProxyField):
        return Mapping(field_type, **kwargs)
    return SimpleMapping(field_type, **kwargs)
