import json
import binascii
import requests
import logging
from flask import jsonify, make_response
from .. import app
from ..settings import app_config
from ..common import error_codes, build_error
import skycoin


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

    # generate CSRF token
    CSRF_token = app.lykke_session.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/csrf")
    ).json()

    if not CSRF_token or "csrf_token" not in CSRF_token:
        return {"status": 500, "error": "Unknown server error"}

    # generate new seed
    new_seed = app.lykke_session.get(
        form_url(
            app_config.SKYCOIN_NODE_URL,
            "/api/v1/wallet/newSeed?entropy=128"
        ),
        headers={'X-CSRF-Token': CSRF_token['csrf_token']}).json()

    if not new_seed or "seed" not in new_seed:
        return {"status": 500, "error": "Unknown server error"}

    # create the wallet from seed
    resp = app.lykke_session.post(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/wallet/create"),
        {
            "seed": new_seed["seed"],
            "label": "wallet123", "scan": "5"
        },
        headers={'X-CSRF-Token': CSRF_token['csrf_token']}
    )

    if not resp:
        return {"status": 500, "error": "Unknown server error"}

    if resp.status_code != 200:
        return {"status": 500, "error": "Unknown server error"}

    new_wallet = resp.json()

    if not new_wallet or "entries" not in new_wallet:
        return {"status": 500, "error": "Unknown server error"}

    seed = new_seed['seed']
    pubkey = skycoin.cipher_PubKey()
    seckey = skycoin.cipher_SecKey()
    error = skycoin.SKY_cipher_GenerateDeterministicKeyPair(
        seed.encode(), pubkey, seckey
    )
    if error != 0:
        return {"status": 500, "error": "Unknown server error"}

    return {
        "privateKey": binascii.hexlify(
            bytearray(seckey.toStr())
        ).decode('ascii'),
        "publicAddress": new_wallet["entries"][0]["address"],
        "addressContext": new_wallet['meta']['filename']
    }


def spend(values):
    """
    Transfer balance
    """
    resp = requests.post(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/wallet/spend"),
        data=values
    )

    if not resp.json:
        return {"status": 500, "error": "Unknown server error"}

    return {"status": resp.status_code, "error": resp.json()["error"]}


def get_version():
    """
    Get blockchain version
    """

    version = app.lykke_session.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/version")
    )

    if not version.json:
        return {"status": 500, "error": "Unknown server error"}

    return version.json()["version"]


def get_balance(address):
    """
    get the balance of given address in blockchain
    """

    values = {"addrs": address}
    balances = app.lykke_session.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/balance"),
        params=values
    )

    if not balances.json:
        return {"status": 500, "error": "Unknown server error"}

    if app.config['DEBUG']:
        logging.debug("Got balance for address")
        logging.debug(balances.json())

    return balances.json()['confirmed']['coins']


def get_balance_scan(address, start_block=1):
    """
    get the balance of given address in blockchain (use block scanning)
    """

    block_count = get_block_count()

    if start_block > block_count:
        return {
            "status": 400,
            "error": "Start block higher that block height",
            "block": block_count
        }
    blocks = get_block_range(start_block, block_count)

    if 'error' in blocks:
        return blocks

    balance = 0
    unspent_outputs = dict()

    for block in blocks:   #: Scan the block range
        for txn in block['body']['txns']:

            inputs = txn['inputs']
            outputs = txn['outputs']

            #: Outgoing
            balance_out = 0
            for input in inputs:
                if input in unspent_outputs:
                    balance_out += unspent_outputs.pop(input)

            #: Incoming
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

    progress = app.lykke_session.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/blockchain/progress")
    )

    return progress.json()['current']


def get_block_range(start_block, end_block):
    """
    returns the blocks from blockchain in the specified range
    """

    values = {"start": start_block, "end": end_block}

    result = app.lykke_session.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/blocks"),
        params=values
    )

    if not result.json:
        return {"status": 500, "error": "Unknown server error"}

    return result.json()['blocks']


def get_block_by_hash(hash):
    """
    returns the blocks from blockchain in the specified range
    """

    values = {"hash": hash}

    result = app.lykke_session.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/block"),
        params=values
    )

    if not result.json:
        return {"status": 500, "error": "Unknown server error"}

    return result.json()


def get_block_by_seq(seqnum):
    """
    returns the blocks from blockchain in the specified range
    """

    values = {"seq": seqnum}

    result = app.lykke_session.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/block"),
        params=values
    )

    if not result.json:
        return {"status": 500, "error": "Unknown server error"}

    return result.json()


def get_address_transactions(address):
    """
    Return the transactions to the specified address
    """

    values = {'confirmed': 1, 'addrs': address}

    result = app.lykke_session.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/transactions"),
        params=values
    )

    if not result.json:
        return {"status": 500, "error": "Unknown server error"}

    return result.json()


def sign_hash(hashHex, seckeyHex):
    seckey = skycoin.cipher_Sig()
    error = skycoin.SKY_cipher_SecKeyFromHex(seckeyHex.encode(), seckey)
    if error != 0:
        return make_response(
            jsonify(
                build_error(
                    'Invalid Input Format',
                    error_codes.badFormat
                )
            ),
            400
        )

    sha256 = skycoin.cipher_SHA256()
    error = skycoin.SKY_cipher_SHA256FromHex(hashHex.encode(), sha256)
    if error != 0:
        return make_response(
            jsonify(
                build_error(
                    'Invalid Input Format',
                    error_codes.badFormat
                )
            ),
            400
        )

    signedHash = skycoin.cipher__Sig()
    error = skycoin.SKY_cipher_SignHash(hash, seckey, signedHash)
    if error != 0:
        return make_response(
            jsonify(
                build_error(
                    'Unknown Server Error',
                    error_codes.unknown
                )
            ),
            500
        )

    error, signedHashHex = skycoin.SKY_cipher_Sig_Hex(signedHash)
    if error != 0:
        return make_response(
            jsonify(
                build_error(
                    'Unknown Server Error',
                    error_codes.unknown
                )
            ),
            500
        )

    retvalue = {
        "signedTransaction": signedHashHex
    }
    return jsonify(retvalue)


def get_unconfirmed_txs():
    """
    get unconfirmed transactions
    """

    resp = requests.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/pendingTxs")
    )
    if not resp:
        return {"status": 500, "error": "Unknown server error"}
    if resp.status_code != 200:
        return {"status": 500, "error": "Unknown server error"}
    return resp.json()


def get_tx_info(txid):
    """
    Get transaction info by id
    """

    values = {"txid": txid}
    resp = requests.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/transaction"),
        params=values
    )
    if not resp.json:
        return {"status": 500, "error": "Unknown server error"}
    return resp.json()


def get_raw_tx(txid):
    """
    Get raw tx by id
    """

    values = {"txid": txid}
    resp = requests.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/rawtx"),
        params=values
    )
    if not resp.json:
        return {"status": 500, "error": "Unknown server error"}
    return resp.json()


def inject_raw_tx(rawtx):
    """
    Broadcasts an encoded transaction to the network
    """

    csrf = requests.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/csrf")
    ).json()

    if not csrf or "csrf_token" not in csrf:
        return {"status": 500, "error": "Unknown server error"}

    resp = requests.post(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/injectTransaction"),
        data=json.dumps(rawtx),
        headers={'X-CSRF-Token': csrf['csrf_token']}
    )
    if resp.status_code == 503:
        return {"status": 503, "error": "Service Unavailable"}
    if not resp.json:
        return {"status": 500, "error": "Unknown server error"}
    return resp.json()


def get_tx_address_related(values):
    """
    Get transactions that are addresses related
    """

    resp = requests.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/transactions"),
        params=values
    )
    if not resp.json:
        return {"status": 500, "error": "Unknown server error"}
    return resp.json()


def resend_unconfirmed_txs():
    """
    Resend unconfirmed transactions
    """

    resp = requests.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/resendUnconfirmedTxns")
    )
    if not resp.json:
        return {"status": 500, "error": "Unknown server error"}
    return resp.json()
