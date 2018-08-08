import os
import hashlib
from enum import Enum


class error_codes(Enum):
    unknown = 1
    amountIsTooSmall = 2
    notEnoughBalance = 3
    missingParameter = 4
    badFormat = 5


def build_error(error_message="", error_code=error_codes.unknown, failed_items={}):
    """
    Generate error message for output
    """
    error_obj = {
        "errorMessage": error_message,
        "errorCode": error_code.name,
        "modelErrors": failed_items
    }

    return error_obj


def generate_hash_key():
    """
    Generate new random hash to be used as key
    """
    m = hashlib.sha256()
    m.update(os.urandom(64))
    return m.hexdigest()
