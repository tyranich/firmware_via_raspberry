def getCrc8(buffer):
    crc = 0
    for cell in buffer:
        crc ^= cell
        for i in range(8):
            crc = ((crc << 1) ^ 0x1d if crc & 0x80 else crc << 1) & 0xff

    return crc