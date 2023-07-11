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

    @staticmethod
    def add_unsigned_bigint_to_bytes(_bytes: bytes, _int: int):
        return _bytes.join(_int.to_bytes(8, "big", signed=False))

    @staticmethod
    def split_bytes_into_list(_bytes: bytes, element_length: int):
        _list = []
        for i in range(0, len(_bytes), element_length):
            _list.append(_bytes[i:i + element_length])
        return _list


    #@staticmethod
    #def day_to_4bytes(day: float):  # returns the day as if it were an int shifted to the left one byte, as the first byte is not significant to the day value
     #   day = day.__int__()
      #  _bytes = day.to_bytes(8, "big", signed=True)
       # return _bytes[3:7]
