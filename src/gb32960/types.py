import locale
import inspect
from datetime import datetime
from typing import Dict
from abc import ABC, abstractmethod

import pytz


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


class NamedNumberField:
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


class Command(NamedNumberField):
    mapping_key = "command_value_text"

    def __init__(self, value):
        super().__init__(value)


CommandVehicleLogin = Command(0x01)
CommandRealtimeData = Command(0x02)
CommandReissueData = Command(0x03)
CommandVehicleLogout = Command(0x04)
CommandPlatformLogin = Command(0x05)
CommandPlatformLogout = Command(0x06)


class ResponseCode(NamedNumberField):
    mapping_key = "response_code_value_text"

    def __init__(self, value):
        super().__init__(value)


ResponseCodeSuccess = ResponseCode(0x01)
ResponseCodeFailure = ResponseCode(0x02)
ResponseCodeVINDuplicated = ResponseCode(0x03)
ResponseCodeCommand = ResponseCode(0xFE)


class EncryptionType(NamedNumberField):
    mapping_key = "encryption_type_value_text"

    def __init__(self, value):
        super().__init__(value)


EncryptionTypeNone = EncryptionType(0x01)
EncryptionTypeRSA = EncryptionType(0x02)
EncryptionTypeAES128 = EncryptionType(0x03)
EncryptionTypeError = EncryptionType(0xFE)
EncryptionTypeNotValid = EncryptionType(0xFF)


class ProtocolObject:
    pass


class AbstractTypeProxy(ABC):
    @abstractmethod
    def value(self):
        pass


class AbstractTypeField(ABC):
    @abstractmethod
    def get_value(self, payload: bytes, offset):
        pass

    @abstractmethod
    def update_offset(self, offset):
        pass


class BytesField(AbstractTypeField):
    creation_counter = 0

    def __init__(self, length, field_type=None):
        self.creation_counter = BytesField.creation_counter
        BytesField.creation_counter += 1
        self.offset = 0
        self.length = length
        self.field_type = field_type

    def get_value(self, payload: bytes, offset):
        if len(payload) < offset + self.length:
            raise ValueError("Payload is not enough")
        target_bytes = payload[offset + self.offset:offset + self.offset + self.length]
        if self.field_type is int:
            return int.from_bytes(target_bytes, "big")
        if self.field_type is str:
            return target_bytes.decode().split("\x00")[0]
        if self.field_type is bytes:
            return target_bytes
        if issubclass(self.field_type, NamedNumberField):
            return self.field_type(int.from_bytes(target_bytes, "big"))
        raise ValueError("Unknown field type")

    def update_offset(self, offset):
        self.offset = offset
        if hasattr(self, "update_fields_offset") and callable(self.update_fields_offset):
            self.update_fields_offset()

    def update_length(self, length):
        self.length = length


class BytesStructWithFieldsProxy(AbstractTypeProxy):
    def __init__(self, payload, offset, fields):
        self.payload = payload
        self.offset = offset
        self.fields = fields

    def get_attr(self, item):
        if item not in self.fields:
            raise AttributeError(f"Attribute {item} not found")
        return self.fields[item].get_value(self.payload, self.offset)

    def __getattr__(self, item):
        return self.get_attr(item)

    def value(self):
        """ get object, will do parse cursive

        :return: final object
        """
        obj = ProtocolObject()
        for k, v in self.fields.items():
            val = v.get_value(self.payload, self.offset)
            if hasattr(val, "value") and callable(val.value):
                val = val.value()
            setattr(obj, k, val)
        return obj


class BytesStructWithFields(BytesField):

    def __init__(self):
        super().__init__(0, Dict)
        self.length = self.payload_length()
        self.offset = 0
        self.update_fields_offset()

    @classmethod
    def get_fields(cls):
        fields = inspect.getmembers(cls, lambda x: isinstance(x, BytesField))
        return sorted(fields, key=lambda x: x[1].creation_counter)

    @classmethod
    def payload_length(cls):
        return sum(map(lambda x: x[1].length, cls.get_fields()))

    @classmethod
    def update_fields_offset(cls):
        offset = 0
        for _, f in cls.get_fields():
            f.update_offset(offset)
            offset += f.length

    def get_value(self, payload: bytes, offset):
        if len(payload) < offset + self.length:
            raise ValueError("Payload is not enough")
        names = dir(self.__class__)
        names = filter(lambda x: isinstance(getattr(self.__class__, x), BytesField), names)
        fields = {}
        for name in names:
            fields[name] = getattr(self.__class__, name)
        return BytesStructWithFieldsProxy(payload, offset + self.offset, fields)


class TimeField(BytesField):
    def __init__(self):
        super().__init__(6)

    def get_value(self, payload: bytes, offset):
        year = ord(payload[offset:offset + 1]) + 2000
        month = ord(payload[offset + 1:offset + 2])
        day = ord(payload[offset + 2:offset + 3])
        hour = ord(payload[offset + 3:offset + 4])
        minute = ord(payload[offset + 4:offset + 5])
        second = ord(payload[offset + 5:offset + 6])
        # utc+8
        return datetime(year, month, day, hour, minute, second, tzinfo=pytz.FixedOffset(480))


TimeType = TimeField()


class Header(BytesStructWithFieldsProxy):
    field_class = None

    def __init__(self, payload, offset, fields):
        super().__init__(payload, offset, fields)

    @property
    def magic(self) -> int:
        return self.get_attr("magic")

    @property
    def command(self) -> Command:
        return self.get_attr("command")

    @property
    def response_code(self) -> ResponseCode:
        return self.get_attr("response_code")

    @property
    def vin(self) -> str:
        return self.get_attr("vin")

    @property
    def encryption_type(self) -> EncryptionType:
        return self.get_attr("encryption_type")

    @property
    def data_length(self) -> int:
        return self.get_attr("data_length")

    @classmethod
    def create(cls, payload, offset) -> "Header":
        if not cls.field_class:
            cls.field_class = HeaderField()
        return cls.field_class.get_value(payload, offset)


class HeaderField(BytesStructWithFields):
    magic = BytesField(2, int)
    command = BytesField(1, Command)
    response_code = BytesField(1, ResponseCode)
    vin = BytesField(17, str)
    encryption_type = BytesField(1, EncryptionType)
    data_length = BytesField(2, int)

    def get_value(self, payload: bytes, offset):
        obj = super().get_value(payload, offset)
        return Header(obj.payload, obj.offset, obj.fields)


class VehicleLoginData(BytesStructWithFieldsProxy):
    def __init__(self, payload, offset, fields):
        super().__init__(payload, offset, fields)

    def chargeable_subsystem_code(self, index):
        if index > self.chargeable_subsystem_count:
            raise ValueError(f"Index out of range, index: {index}, count: {self.chargeable_subsystem}")
        payload, offset, _ = self.chargeable_subsystem_codes
        offset += index * self.chargeable_subsystem_code_length
        return BytesField(self.chargeable_subsystem_code_length, str).get_value(payload, offset)


class VehicleLoginDataField(BytesStructWithFields):
    time = TimeField()
    serial = BytesField(2)
    iccid = BytesField(20, str)
    chargeable_subsystem_count = BytesField(1, str)
    chargeable_subsystem_code_length = BytesField(1, str)
    chargeable_subsystem_codes = BytesField(0)

    def get_value(self, payload: bytes, offset):
        obj = super().get_value(payload, offset)
        obj["chargeable_subsystem_codes"] = BytesField(
            obj.chargeable_subsystem_count * obj.chargeable_subsystem_code_length
        )
        return VehicleLoginData(obj.payload, obj.offset, obj.fields)


class Packet:

    def __init__(self, payload: bytes, offset):
        self.header = HeaderField.get_value(payload, offset)
        self.data_offset = offset + 24
        self.data_length = self.header.data_length
        self.bcc = payload[offset + 24 + self.data_length]
        self.payload = payload

    @property
    def data_raw(self):
        return self.payload[self.data_offset:self.data_offset + self.data_length]

    @property
    def data(self):
        return None
