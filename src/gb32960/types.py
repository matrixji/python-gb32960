import locale


class Helper:
    @classmethod
    def load_mappings(cls, name):
        local_name = "".join(locale.getdefaultlocale())
        # remove - and _
        local_name = local_name.replace("-", "").replace("_", "").lower()
        try:
            module = __import__(f"protocol_text_locales.{local_name}")
        except ImportError:
            module = __import__("protocol_text_locales.default")
        return getattr(module, name)

    @classmethod
    def get_text_by_value(cls, mapping_key, value):
        data = Helper.load_mappings(mapping_key)
        if value in data:
            return data[value]
        value = "Unknown"
        key_range = 0xffffffff
        for k, v in data.items():
            if isinstance(k, tuple) and len(k) == 2 and k[0] <= value <= k[1]:
                if k[1] - k[0] < key_range:
                    key_range = k[1] - k[0]
                    value = v
        return value


class DataWithText:
    mapping_key = ""

    def __init__(self, value):
        self.value = value
        self.text_ = None

    def __eq__(self, other):
        return self.value == other.value

    @property
    def text(self):
        if self.text_ is None:
            self.text_ = Helper.get_text_by_value(self.mapping_key, self.value)
        return self.text_


class Command(DataWithText):
    mapping_key = "command_value_text"

    def __init__(self, value):
        super().__init__(value)


CommandVehicleLogin = Command(0x01)
CommandRealtimeData = Command(0x02)
CommandReissueData = Command(0x03)
CommandVehicleLogout = Command(0x04)
CommandPlatformLogin = Command(0x05)
CommandPlatformLogout = Command(0x06)


class ResponseCode(DataWithText):
    mapping_key = "response_code_value_text"

    def __init__(self, value):
        super().__init__(value)


ResponseCodeSuccess = ResponseCode(0x01)
ResponseCodeFailure = ResponseCode(0x02)
ResponseCodeVINDuplicated = ResponseCode(0x03)
ResponseCodeCommand = ResponseCode(0xFE)


class EncryptionType(DataWithText):
    mapping_key = "encryption_type_value_text"

    def __init__(self, value):
        super().__init__(value)


EncryptionTypeNone = EncryptionType(0x01)
EncryptionTypeRSA = EncryptionType(0x02)
EncryptionTypeAES128 = EncryptionType(0x03)
EncryptionTypeError = EncryptionType(0xFE)
EncryptionTypeNotValid = EncryptionType(0xFF)



class Header:
    header_length = 24

    def __init__(self, *args, **kwargs):
        self.bytes = None
        if "payload" in kwargs:
            self.payload = kwargs["payload"]

    def load_bytes(self, payload: bytes):
        self.payload = payload[:24]

    @property
    def magic(self) -> bytes:
        return self.payload[:2]

    @property
    def command(self) -> Command:
        return Command(int.from_bytes(self.payload[2:3]))

    @property
    def response_code(self) -> ResponseCode:
        return ResponseCode(int.from_bytes(self.payload[3:4]))

    @property
    def vin(self) -> str:
        return self.payload[4:21].decode("utf-8")

    @property
    def encryption_type(self) -> EncryptionType:
        return EncryptionType(int.from_bytes(self.payload[21:22]))

    @property
    def data_length(self) -> int:
        return int.from_bytes(self.payload[22:24])
