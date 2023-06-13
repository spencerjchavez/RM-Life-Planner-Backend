# CREATED JUNE OF 2023 BY SPENCER CHAVEZ

class BytesHelper:
    @staticmethod
    def remove_unsigned_int_from_bytes(_bytes: bytes, _int: int):
        int_bytes = _int.to_bytes(4, "big", signed=False)
        index = 0
        while True:
            index = _bytes.find(int_bytes, index)
            if index == -1:
                return None
            if index % 4 == 0:
                return _bytes[:index] + _bytes[index + 4:]
            index += 1

    @staticmethod
    def add_unsigned_int_to_bytes(_bytes: bytes, _int: int):
        return _bytes.join(_int.to_bytes(4, "big", signed=False))

