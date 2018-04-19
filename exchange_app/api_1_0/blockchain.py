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


def get_balance_scan(address, start_block = 1):
    """
    get the balance of given address in blockchain (use block scanning)
    """

    block_count = get_block_count()

    if start_block > block_count:
        return {"status": 400, "error": "Start block higher that block height", 'block': block_count}

        
    blocks = get_block_range(start_block, block_count)
    
    if 'error' in blocks:
        return blocks
    
    balance = 0
    unspent_outputs = dict()
    
    for block in blocks:   #Scan the block range
        for txn in block['body']['txns']:
            
            inputs = txn['inputs']
            outputs = txn['outputs']
            
            #Outgoing
            balance_out = 0
            for input in inputs:
                if input in unspent_outputs:
                    balance_out += unspent_outputs.pop(input)
                    
            #Incoming
            balance_in = 0
            for output in outputs:
                if output['dst'] == address:
                    balance_in += float(output['coins'])
                    unspent_outputs[output['uxid']] = float(output['coins'])

                    
            balance += balance_in
            balance -= balance_out
    
    return {'balance': balance, 'block': block_count}
    
    
def get_block_count():
    """
    Get the current block height of blockchain
    """
    progress = requests.get(form_url(app_config.SKYCOIN_NODE_URL, "/blockchain/progress"))

    return progress.json()['current']


def get_block_range(start_block, end_block):
    """
    returns the blocks from blockchain in the specified range
    """
    
    values = {"start": start_block, "end": end_block}
    result = requests.get(form_url(app_config.SKYCOIN_NODE_URL, "/blocks"), params=values)
    
    if not result.json:
        return {"status": 500, "error": "Unknown server error"}
        
    return result.json()['blocks']
     

def get_block_by_hash(hash):
    """
    returns the blocks from blockchain in the specified range
    """
    
    values = {"hash": hash}
    result = requests.get(form_url(app_config.SKYCOIN_NODE_URL, "/block"), params=values)
    
    if not result.json:
        return {"status": 500, "error": "Unknown server error"}
        
    return result.json()
    
    
def get_block_by_seq(seqnum):
    """
    returns the blocks from blockchain in the specified range
    """
    
    values = {"seq": seqnum}
    result = requests.get(form_url(app_config.SKYCOIN_NODE_URL, "/block"), params=values)
    
    if not result.json:
        return {"status": 500, "error": "Unknown server error"}
        
    return result.json()