import os
import hashlib
from enum import Enum
from flask import Blueprint, jsonify
import requests
from .settings import app_config
import json

api = Blueprint('api', __name__)

class error_codes(Enum):
    unknown = 1
    amountIsTooSmall = 2
    notEnoughBalance = 3
    missingParameter = 4
    badFormat = 5


def build_error(error_message="", error_code = error_codes.unknown, failed_items={}):
    """
    Generate error message for output
    """
    error_obj = {"errorMessage": error_message,
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

def form_url(base, path):
    """
    Conform the full URL from base URL and path
    """

    if path[0] != '/':
        path = '/' + path

    if base[len(base) - 1] == '/':
        base = base[0:len(base) - 1]

    url = base + path

    return url


def get_url(path, values=""):
    """
    General GET function for blockchain
    """

    url = form_url(app_config.SKYCOIN_NODE_URL, path)

    # resp = requests.get(url, params = values)
    # response_data = resp.json()

    response_data = {"Called": "get_url()", "url": url, "values:": values}

    return response_data


def post_url(path, values=""):
    """
    General POST function for blockchain
    """

    url = form_url(app_config.SKYCOIN_NODE_URL, path)

    # resp = requests.post(url, data = values)
    # response_data = resp.json()

    response_data = {"Called": "post_url()", "url": url, "values:": values}

    return response_data

def get_transaction_context(tx):
	#TODO: Find a more ellegant way to create the context
	return json.dumps(tx)

def get_transaction_from_context(context):
    try:
        return json.loads(context)
    except:
        return False
