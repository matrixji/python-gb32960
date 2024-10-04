command_value_text = {
    0x01: "VehicleLogin",
    0x02: "RealtimeData",
    0x03: "ReissueData",
    0x04: "VehicleLogout",
    0x05: "PlatformLogin",
    0x06: "PlatformLogout",
    (0x07, 0x08): "Terminal Data Reserved",
    (0x09, 0x7F): "Upstream Data Reserved",
    (0x80, 0x82): "Terminal Data Reserved",
    (0x83, 0xBF): "Downstream Data Reserved",
    (0xC0, 0xFE): "Customized",
}

response_code_value_text = {
    0x01: "Success",
    0x02: "Failure",
    0x03: "VIN Duplicated",
    0xFE: "Command",
}

encryption_type_value_text = {
    0x01: "None",
    0x02: "RSA",
    0x03: "AES128",
    0xFE: "Error",
    0xFF: "Not Valid",
}
