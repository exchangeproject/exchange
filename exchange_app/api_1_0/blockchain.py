
import binascii
import logging
from .. import app
from ..settings import app_config
from time import perf_counter
from ..common import form_url, get_url, post_url
import skycoin
from flask import jsonify
import json
import codecs

def get_version():
    """
    Get blockchain version
    """

    version = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/version"),
        verify = app_config.VERIFY_SSL)

    if not version.json:
        return {"status": 500, "error": "Unknown server error"}

    return version.json()["version"]


def get_balance(address):
    """
    get the balance of given address in blockchain
    """

    values = {"addrs": address}
    balances = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/balance"),
        verify = app_config.VERIFY_SSL, params=values)

    if not balances.json:
        return {"status": 500, "error": "Unknown server error"}

    if app.config['DEBUG']:
        logging.debug("Got balance for address")
        logging.debug(str(balances))

    try:
        return {'balance' : int(balances.json()['confirmed']['coins'])}
    except:
        return {"status": 500, "error": "Unknown server error"}


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

    progress = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/blockchain/progress"),
        verify = app_config.VERIFY_SSL)

    return progress.json()['current']


def get_block_range(start_block, end_block):
    """
    returns the blocks from blockchain in the specified range
    """

    values = {"start": start_block, "end": end_block}

    result = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/blocks"),
        verify = app_config.VERIFY_SSL, params=values)

    if not result.json:
        return {"status": 500, "error": "Unknown server error"}

    return result.json()['blocks']


def get_block_by_hash(hash):
    """
    returns the blocks from blockchain in the specified range
    """

    values = {"hash": hash}

    result = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/block"),
        verify = app_config.VERIFY_SSL, params=values)

    if not result.json:
        return {"status": 500, "error": "Unknown server error"}

    return result.json()


def get_block_by_seq(seqnum):
    """
    returns the blocks from blockchain in the specified range
    """

    values = {"seq": seqnum}

    result = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/block"),
        verify = app_config.VERIFY_SSL, params=values)

    if not result.json:
        return {"status": 500, "error": "Unknown server error"}

    return result.json()


def get_address_transactions(address):
    """
    Return the transactions to the specified address
    """

    values = {'confirmed': 1, 'addrs': address}

    result = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/transactions"),
        verify = app_config.VERIFY_SSL, params=values)

    if not result.json:
        return {"status": 500, "error": "Unknown server error"}

    return result.json()

def transaction_many_inputs(values):
    """
    build a transaction with many inputs
    """
    csrf = requests.get(form_url(base_url, "/csrf")).json()
    if not csrf or "csrf_token" not in csrf:
        return {"status": 500, "error": "Unknown server error"}
    resp = requests.post(
        form_url(base_url, "/transactions/many-inputs"),
        data=values,
        headers={'X-CSRF-Token': csrf['csrf_token']}
    )
    if not resp:
        return {"status": 500, "error": "Unknown server error"}
    if resp.status_code != 200:
        return {"status": 500, "error": "Unknown server error"}
    return resp.json()


def transaction_many_outputs(values):
    """
    build a transaction with many outputs
    """
    csrf = requests.get(form_url(base_url, "/csrf")).json()
    if not csrf or "csrf_token" not in csrf:
        return {"status": 500, "error": "Unknown server error"}
    resp = requests.post(
        form_url(base_url, "/transactions/many-outputs"),
        data=values,
        headers={'X-CSRF-Token': csrf['csrf_token']}
    )
    if not resp:
        return {"status": 500, "error": "Unknown server error"}
    if resp.status_code != 200:
        return {"status": 500, "error": "Unknown server error"}
    return resp.json()

def transaction_broadcast(signedTransaction):
    # generate CSRF token
    CSRF_token = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/csrf"),
        verify = app_config.VERIFY_SSL).json()
    if not CSRF_token or "csrf_token" not in CSRF_token:
        logging.debug('transaction_broadcast - Error trying to get CSRF token')
        return {"status": 500, "error": "Unknown server error"}
    #broadcast transaction
    resp = app.lykke_session.post(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/injectTransaction"),
         json.dumps({"rawtx": signedTransaction}),
         headers={'X-CSRF-Token': CSRF_token['csrf_token'],
         "Content-Type" : "application/json"},
         verify = app_config.VERIFY_SSL)
    if not resp:
        return {"status": 500, "error": "Unknown server error"}
    if resp.status_code != 200:
        return {"status": 500, "error": "Unknown server error"}
    result = resp.json()
    return result

#Check balances for a transaction
def check_balance_from_transaction(tx):
    result = get_balance(tx['fromAddress'])
    if 'error' in result:
        logging.debug('check_balance_from_transaction - Error ' + result['error'])
        return False, 500, "Unknown server error"
    balance = result['balance']
    amount = 0
    for output in tx['outputs']:
        amount += output['amount']
    if balance < amount:
        logging.debug('check_balance_from_transaction - Not enough balance')
        return False, 400, "Not enough balance"
    return True, 0, ""

# Creates a transaction
# Calls skycoin node to create the transactions
# Skycoin returns a signed transactions
# Then signing is removed
def create_transaction(tx, min_output_hours=0):
    #generate CSRF token
    CSRF_token = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/csrf"),
        verify = app_config.VERIFY_SSL).json()
    if not CSRF_token or "csrf_token" not in CSRF_token:
        logging.debug('create_transaction - Error trying to get CSRF token')
        return {"status": 500, "error": "Unknown server error"}
    outputs = []
    total_amount = 0
    for output in tx['outputs']:
        dest = {
        	"address": output['toAddress'],
        	"coins": "{:f}".format(output['amount'])
        }
        total_amount += output['amount']
        outputs.append(dest)
    data = {
    	"hours_selection": {
        	"type": "auto",
        	"mode": "share",
        	"share_factor": "0.5"
    	},
    	"wallet": {
        	"id": tx['fromAddressContext']
    	},
    	"to": outputs
    }
    if min_output_hours > 0:
        output = _pickOutputFromAddress(tx['fromAddress'],
            total_amount, min_output_hours)
        if output != '':
            data["wallet"]["unspents"] = [output]
        else:
            min_output_hours = 0
    if min_output_hours <= 0:
        data["wallet"]["addresses"] = [tx['fromAddress']]
    logging.debug("Creating transaction")
    response = app.lykke_session.post(form_url(app_config.SKYCOIN_NODE_URL,
            '/api/v1/wallet/transaction'),
            data=json.dumps(data),
            headers={'X-CSRF-Token': CSRF_token['csrf_token'],
            "Content-Type" : "application/json"},
            verify = app_config.VERIFY_SSL)
    if response.status_code == 200:
        json_response = response.json()
        logging.debug("Response from '/api/v1/wallet/transaction: {}".format(str(json_response)))
        if not 'error' in json_response:
            if 'encoded_transaction' in json_response:
                ok, tx = _removeSigningFromTransaction(json_response['encoded_transaction'])
                if ok:
                    return {"encoded_transaction" : tx}
                else:
                    logging.debug('create_transaction - Failed at removing signature from transaction"}')
                    return {"status": 500, "error": "Error creating transaction in Skycoin"}
        logging.debug('create_transaction - Invalid response from /api/v1/wallet/transaction"}')
        return {"status": 500, "error": "Invalid response from /api/v1/wallet/transaction"}
    else:
        logging.debug('create_transaction - Error creating transaction in Skycoin :{}'.format(str(response)))
        return {"status": response.status_code, "error": "Error creating transaction in Skycoin"}


def _removeSigningFromTransaction(hexencoded_transaction):
    transaction_handle = 0
    try:
        serialized = codecs.decode(hexencoded_transaction, 'hex')
        error, transaction_handle = skycoin.SKY_coin_TransactionDeserialize(serialized)
        if error != 0:
            logging.debug("SKY_coin_TransactionDeserialize failed. Error: {}".format(error))
            return False, ""
        error = skycoin.SKY_coin_Transaction_ResetSignatures(transaction_handle, 0)
        if error != 0:
            logging.debug("SKY_coin_Transaction_ResetSignatures failed. Error: {}".format(error))
            return False, ""
        error, serialized = skycoin.SKY_coin_Transaction_Serialize(transaction_handle)
        if error != 0:
            logging.debug("SKY_coin_Transaction_Serialize failed. Error: {}".format(error))
            return False, ""
        return True, codecs.encode(serialized, 'hex')
    except Exception as e:
        logging.debug("Failed at removing transaction. {}".format(str(e)))
        return False, ""
    finally:
        if transaction_handle != 0:
            skycoin.SKY_handle_close(transaction_handle)

#When making tests picking an output to spend
#that will allow subsequent transactions
def _pickOutputFromAddress(address, min_amount, minimum = 32):
    #Pick the output with less coin hours
    #but with at least 10 to be able to
    #return SKY to original address
    data = {"addrs" : address}
    resp = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL,
        "api/v1/outputs"),
        params=data,
        verify = app_config.VERIFY_SSL)
    if resp.status_code != 200:
        logging.debug("Error getting outputs for address: {}. {}",
            address, resp.text)
        return ''
    result = resp.json()
    if "error" in result:
        logging.debug("Error getting outputs for address: {}. Error: {}",
            address, result["error"]["message"])
        return ''
    min_hours = 1000000000
    hash = ''
    for output in result["head_outputs"]:
        hours = output['hours']
        coins = float(output['coins'])
        if coins >= min_amount and hours >= minimum and hours < min_hours:
            min_hours = hours
            hash = output['hash']
    logging.debug("Picked output {} with {} hours".format(hash, min_hours))
    return hash
