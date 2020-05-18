import string
import random
import hashlib


def generate_rand_code(code_size = 6, seed_chars=string.ascii_uppercase + string.digits):
    """ Generates a random, alpha-numeric code """
    return ''.join(random.choice(seed_chars) for _ in range(code_size))


def generate_hash_sha512(seed = generate_rand_code(32)):
    """ Generates a Sha512 hash """
    return hashlib.sha512(seed.encode('utf-8')).hexdigest()
