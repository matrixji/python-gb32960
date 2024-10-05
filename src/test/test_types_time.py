from gb32960.types import TimeField
from datetime import timedelta

def test_time_fields():
    buff = b"\x01\x02\x03\x04\x05\x06"
    time_field = TimeField().get_value(buff, 0)
    assert time_field.year == 2001
    assert time_field.month == 2
    assert time_field.day == 3
    assert time_field.hour == 4
    assert time_field.minute == 5
    assert time_field.second == 6
    # gb32960 using Beijing time
    assert time_field.utcoffset() == timedelta(hours=8)
