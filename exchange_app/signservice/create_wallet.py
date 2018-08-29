import binascii
import logging
from .. import app
from ..settings import app_config
from ..common import form_url, get_url, post_url
import skycoin

def create_wallet():
    """
    Create the wallet in blockchain
    """

    # generate new seed
    new_seed = app.lykke_session.get(
        form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/wallet/newSeed?entropy=128"),
        verify = app_config.VERIFY_SSL).json()

    if not new_seed or "seed" not in new_seed:
        return {"status": 500, "error": "Unknown server error"}

	# generate CSRF token
    CSRF_token = app.lykke_session.get(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/csrf"),
        verify = app_config.VERIFY_SSL).json()

    if not CSRF_token or "csrf_token" not in CSRF_token:
        return {"status": 500, "error": "Unknown server error"}

    # create the wallet from seed
    resp = app.lykke_session.post(form_url(app_config.SKYCOIN_NODE_URL, "/api/v1/wallet/create"),
                         {"seed": new_seed["seed"],
                             "label": "wallet123", "scan": "5"},
                         headers={'X-CSRF-Token': CSRF_token['csrf_token']},
                         verify = app_config.VERIFY_SSL)

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
            seed.encode(), pubkey, seckey)
    if error != 0:
        return {"status": 500, "error": "Unknown server error"}

    return {
        "privateKey": binascii.hexlify(bytearray(seckey.toStr())).decode('ascii'),
        "publicAddress": new_wallet["entries"][0]["address"],
        "addressContext": new_wallet['meta']['filename']
    }
