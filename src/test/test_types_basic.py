import pytest
from gb32960.types import BytesField, BytesStructWithFields


class TestBytesField:
    def test_get_value(self):
        field = BytesField(2, int)
        assert field.get_value(b"\x01\x02", 0) == 0x0102
        field = BytesField(2, str)
        assert field.get_value(b"\x01\x02", 0) == "\x01\x02"
        with pytest.raises(ValueError):
            field = BytesField(2, float)
            field.get_value(b"\x01\x02", 0)

    def test_update_offset(self):
        field = BytesField(2)
        field.update_offset(2)
        assert field.offset == 2


class FooFields(BytesStructWithFields):
    a = BytesField(2, int)
    b = BytesField(2, int)
    c = BytesField(4, str)
    d = BytesField(2, int)


class BarFields(BytesStructWithFields):
    x = BytesField(2, int)
    y = FooFields()
    z = BytesField(2, int)


class TestBytesStructWithFields:
    def test_length(self):
        assert FooFields.payload_length() == 10
        assert BarFields.payload_length() == 14

    def test_foo(self):
        buff = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A"
        foo = FooFields().get_value(buff, 0)
        assert foo.a == 0x0102
        assert foo.b == 0x0304
        assert foo.c == "\x05\x06\x07\x08"
        assert foo.d == 0x090A

    def test_bar(self):
        buff = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E"
        bar = BarFields().get_value(buff, 0)
        assert bar.x == 0x0102
        assert bar.y.a == 0x0304
        assert bar.y.b == 0x0506
        assert bar.y.c == "\x07\x08\x09\x0A"
        assert bar.y.d == 0x0B0C
        assert bar.z == 0x0D0E
