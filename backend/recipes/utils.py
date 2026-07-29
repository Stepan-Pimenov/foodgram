import string

BASE36_ALPHABET = string.digits + string.ascii_lowercase


def to_base36(number):
    if number == 0:
        return '0'
    result = ''
    while number:
        number, remainder = divmod(number, 36)
        result = BASE36_ALPHABET[remainder] + result
    return result
