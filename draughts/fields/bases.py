from abc import ABC
from typing import Tuple, Any, Iterable, Sequence


class Field:
    """An abstract data field for a model."""
    def __init__(self, **kwargs):
        self.metadata = kwargs
        self.metadata_defaults = {}
        self.name = None

    def __contains__(self, item):
        return item in self.metadata or item in self.metadata_defaults

    def __getitem__(self, item):
        return self.metadata.get(item, self.metadata_defaults.get(item))

    def cast(self, value):
        raise NotImplementedError()

    def sample(self):
        """Generate a random value appropriate for this field."""
        raise NotImplementedError(self.__class__)


class MultivaluedField(Field):
    """A base for fields where the value could have many parts, but don't require a proxy."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def cast(self, value):
        raise NotImplementedError()

    def sample(self):
        raise NotImplementedError()

    def flat_fields(self, prefix):
        raise NotImplementedError()


class ProxyField(Field):
    """A base for fields where the underlying data and the 'view' are different."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def cast(self, value) -> Tuple[Any, Any]:
        """Convert value into the type for this field.

        The cast method for proxy is special in that it returns two things:
            - The proxy object that code interacts with
            - The underlying data object that will occupy the field in the parent dictionary.

        The proxy is responsible for making sure what it presents is kept up to
        date with whatever is returned from this method for data. For example, the list
        and mapping proxy objects return proxies that wrap a dictionary or list object
        that are returned as the second parameter.

        Proxy fields need to have matching names, and any complex data has to be
        contained within the field itself (this is opposed to MultiFields where the
        opposite is true)
        """
        raise NotImplementedError()

    def sample(self):
        raise NotImplementedError()

    def flat_fields(self, prefix):
        raise NotImplementedError()


class MultiField(Field):
    """A field that actually represents several hidden entries in the model.

    Uses a proxy similar to a proxy field, but doesn't have its own internal
    data structure, instead relying on storing data in the parent structure.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def cast(self, value) -> Sequence:
        """Convert an assigned value into a sequence of values suitable to pass to proxy."""
        raise NotImplementedError()

    def proxy(self, parent, values):
        """Construct a proxy over the values given.

        The values will which will match in order the keys produced by 'components'.

        Either this method or the proxy object is responsible for setting the
        values it is constructed with into the parent in the corresponding fields.

        If this method does it, the proxy should be something immutable, if its not
        immutable, then the proxy is responsible for retaining a reference to parent
        and keeping the parent synced with the view of it.
        """
        raise NotImplementedError()

    def sample(self):
        """Return an (ideally random) object that would be appropriate as an argument to cast."""
        raise NotImplementedError()

    def components(self):
        """Return the keys for the components.

        This must be the same every time this is called for a given field.
        """
        raise NotImplementedError()
