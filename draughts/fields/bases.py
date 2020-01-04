
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

    def cast(self, value):
        raise NotImplementedError()

    def sample(self):
        raise NotImplementedError()

    def flat_fields(self, prefix):
        raise NotImplementedError()
