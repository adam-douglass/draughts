from .basic import Boolean, Integer, Float, Timestamp, Enum, Bytes
from .basic import String, Keyword, Text, JSON, UUID, DateString, SeparatedFraction
from .basic import Any
from .pattern import PatternString, MD5, SHA256, PhoneNumber, MACAddress, PrivateIP, SSDeepHash, IP, \
    Domain, Email, SHA1, URI, URIPath
from .complex import Compound
from .bases import MultivaluedField, ProxyField
from .multivalued import SimpleList, SimpleMapping
from .complex import List as CompoundList, Mapping as CompoundMapping


def List(field_type, **kwargs):
    """A helper "class" to choose the right list class for a given field."""
    if isinstance(field_type, ProxyField):
        return CompoundList(field_type, **kwargs)
    return SimpleList(field_type, **kwargs)


ListTypes = (CompoundList, SimpleList)


def Mapping(field_type, **kwargs):
    """A helper "class" to choose the right list class for a given field."""
    if isinstance(field_type, ProxyField):
        return CompoundMapping(field_type, **kwargs)
    return SimpleMapping(field_type, **kwargs)


MappingTypes = (CompoundMapping, SimpleMapping)
