import requests
import logging
from .. import app
from ..settings import app_config


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


def create_wallet():
    """
    Create the wallet in blockchain
    """

    # generate new seed
    new_seed = requests.get(form_url(app_config.SKYCOIN_NODE_URL, "/wallet/newSeed")).json()

    if not new_seed or "seed" not in new_seed:
        return {"status": 500, "error": "Unknown server error"}

    # generate CSRF token
    CSRF_token = requests.get(form_url(app_config.SKYCOIN_NODE_URL, "/csrf")).json()

    if not CSRF_token or "csrf_token" not in CSRF_token:
        return {"status": 500, "error": "Unknown server error"}

    # create the wallet from seed
    # TODO: Where to get labels? How about scan?
    resp = requests.post(form_url(app_config.SKYCOIN_NODE_URL, "/wallet/create"),
                         {"seed": new_seed["seed"],
                             "label": "wallet123", "scan": "5"},
                         headers={'X-CSRF-Token': CSRF_token['csrf_token']})

    if not resp:
        return {"status": 500, "error": "Unknown server error"}

    if resp.status_code != 200:
        return {"status": 500, "error": "Unknown server error"}

    new_wallet = resp.json()

    if not new_wallet or "entries" not in new_wallet:
        return {"status": 500, "error": "Unknown server error"}

    return {
        "privateKey": new_wallet["entries"][0]["secret_key"],
        "address": new_wallet["entries"][0]["address"]
    }

def spend(values):
    """
    Transfer balance
    """
    resp = requests.post(form_url(app_config.SKYCOIN_NODE_URL, "/wallet/spend"), data=values)

    if not resp.json:
        return {"status": 500, "error": "Unknown server error"}

    return {"status": resp.status_code, "error": resp.json()["error"]}


def get_version():
    """
    Get blockchain version
    """

    version = requests.get(form_url(app_config.SKYCOIN_NODE_URL, "/version"))

    if not version.json:
        return {"status": 500, "error": "Unknown server error"}

    return version.json()["version"]


def get_balance(address):
    """
    get the balance of given address in blockchain
    """

    values = {"addrs": address}
    balances = requests.get(form_url(app_config.SKYCOIN_NODE_URL, "/balance"), params=values)

    if not balances.json:
        return {"status": 500, "error": "Unknown server error"}

    if app.config['DEBUG']:
        logging.debug("Got balance for address")
        logging.debug(balances.json())

    return balances.json()['confirmed']['coins']


def get_transactions_from(address, afterhash):
    """
    return all transactions from address after the one specified by afterhash
    """

    #TODO: Read this from blockchain

    transfers = [
        {"operationId": "guid", #TODO: Where to get this. If is only valid for this app's transactions, when do we generate/store it? Can blockchain provide it?
         "timestamp": "20071103T161805Z", #TODO: confirm if should use ISO-8601 basic or extended timestamp representation
         "fromAddress": address,
         "toAddress": "xxxxxx",
         "assetId": "skycoin",
         "amount": "1000000",
         "hash": "qwertyasdfg"
        },
        {"operationId": "guid",
         "timestamp": "20180215T231403Z",
         "fromAddress": address,
         "toAddress": "xxxxxx",
         "assetId": "skycoin",
         "amount": "2000000",
         "hash": "asdfgzxcvb"
        }
    ]

    return transfers

def get_transactions_to(address, afterhash):
    """
    return all transactions to address after the one specified by afterhash
    """

    #TODO: Read this from blockchain

    transfers = [
        {"operationId": "guid", #TODO: Where to get this. If is only valid for this app's transactions, when do we generate/store it? Can blockchain provide it?
         "timestamp": "20071103T161805Z", #TODO: confirm if should use ISO-8601 basic or extended timestamp representation
         "fromAddress": "xxxxxx",
         "toAddress": address,
         "assetId": "skycoin",
         "amount": "1000000",
         "hash": "qwertyasdfg"
        },
        {"operationId": "guid",
         "timestamp": "20180215T231403Z",
         "fromAddress": "xxxxxx",
         "toAddress": address,
         "assetId": "skycoin",
         "amount": "2000000",
         "hash": "asdfgzxcvb"
        }
    ]

    return transfers
