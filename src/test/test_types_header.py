from gb32960.types import Header, CommandVehicleLogin, ResponseCodeSuccess, EncryptionTypeNone


class TestHeader:
    buff_text = "\x23\x23\x01\x01VIN1234567890ABCD\x01\x00\x00"

    def test_generic(self):
        buff = TestHeader.buff_text.encode()
        header = Header.create(buff, 0)
        assert header.magic == 0x2323
        assert header.command == CommandVehicleLogin
        assert header.response_code == ResponseCodeSuccess
        assert header.vin == "VIN1234567890ABCD"
        assert header.encryption_type == EncryptionTypeNone
        assert header.data_length == 0
