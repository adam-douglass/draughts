import re
import rstr
from .basic import String


class PatternString(String):
    def __init__(self, pattern, **kwargs):
        super().__init__(**kwargs)
        self.pattern = re.compile(pattern)

    def cast(self, value):
        value = super().cast(value)
        if not self.pattern.fullmatch(value):
            raise ValueError(f"Illegal value for {self.__class__.__name__} {value}")
        return value

    def sample(self):
        return rstr.xeger(self.pattern)


class FixedPatternString(PatternString):
    REGEX = None
    def __init__(self, **kwargs):
        super().__init__(self.REGEX, **kwargs)


class MD5(FixedPatternString):
    REGEX = r"^[a-f0-9]{32}$"


class SHA1(FixedPatternString):
    REGEX = r"^[a-f0-9]{40}$"


class SHA256(FixedPatternString):
    REGEX = r"^[a-f0-9]{64}$"


class SSDeepHash(FixedPatternString):
    REGEX = r"^[0-9]{1,18}:[a-zA-Z0-9/+]{0,64}:[a-zA-Z0-9/+]{0,64}$"


class Domain(FixedPatternString):
    REGEX = r"(?:(?:[A-Za-z0-9\u00a1-\uffff][A-Za-z0-9\u00a1-\uffff_-]{0,62})?[A-Za-z0-9\u00a1-\uffff]\.)+" \
            r"(?:xn--)?(?:[A-Za-z0-9\u00a1-\uffff]{2,}\.?)"


class Email(FixedPatternString):
    REGEX = f"^[a-zA-Z0-9!#$%&'*+/=?^_‘{{|}}~-]+(?:\\.[a-zA-Z0-9!#$%&'*+/=?^_‘{{|}}~-]+)*@{Domain.REGEX}$"


class IP(FixedPatternString):
    REGEX = r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"


class PrivateIP(FixedPatternString):
    REGEX = r"(?:(?:127|10)(?:\.(?:[2](?:[0-5][0-5]|[01234][6-9])|[1][0-9][0-9]|[1-9][0-9]|[0-9])){3})|" \
            r"(?:172\.(?:1[6-9]|2[0-9]|3[0-1])(?:\.(?:2[0-4][0-9]|25[0-5]|[1][0-9][0-9]|[1-9][0-9]|[0-9])){2}|" \
            r"(?:192\.168(?:\.(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])){2}))"


class PhoneNumber(FixedPatternString):
    REGEX = r"^(\+?\d{1,2})?[ .-]?(\(\d{3}\)|\d{3})[ .-](\d{3})[ .-](\d{4})$"


class MACAddress(FixedPatternString):
    REGEX = r"^(?:(?:[0-9a-f]{2}-){5}[0-9a-f]{2}|(?:[0-9a-f]{2}:){5}[0-9a-f]{2})$"


class URIPath(FixedPatternString):
    REGEX = r"(?:[/?#]\S*)"


class URI(FixedPatternString):
    REGEX = f"^((?:(?:[A-Za-z]*:)?//)?(?:\\S+(?::\\S*)?@)?(?:{IP.REGEX}|{Domain.REGEX})(?::\\d{{2,5}})?){URIPath.REGEX}?$"
