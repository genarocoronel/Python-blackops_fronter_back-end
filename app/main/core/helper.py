import string
import random
import hashlib


def generate_rand_code(code_size = 6, seed_chars=string.ascii_uppercase + string.digits):
    """ Generates a random, alpha-numeric code """
    return ''.join(random.choice(seed_chars) for _ in range(code_size))


def generate_hash_sha512(seed = generate_rand_code(32)):
    """ Generates a Sha512 hash """
    return hashlib.sha512(seed.encode('utf-8')).hexdigest()


def is_boolean(value):
    if value is None:
        return False

    if isinstance(value, str) and (value.lower() == 'true' or value.lower() == 'false'):
        return True

    if isinstance(value, bool):
        return True

    return False


def convert_to_boolean(value):
    return is_true(value)


def is_true(value):
    if value is None:
        return False

    if isinstance(value, str) and value.lower() == 'true':
        return True

    if isinstance(value, bool):
        return value

    return False
