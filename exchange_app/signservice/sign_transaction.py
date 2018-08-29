from .. import app
from ..settings import app_config
from ..common import build_error, form_url, get_url, post_url
import json
from ..validate import validate_sign_transaction
from flask import jsonify, request, make_response
import logging
import codecs
import skycoin

def sign_transaction(txContext, privateKeys):
    transaction_handle = 0
    try:
        assert len(privateKeys) > 0
        serialized = codecs.decode(txContext, 'hex')
        error, transaction_handle = skycoin.SKY_coin_TransactionDeserialize(serialized)
        if error != 0:
            logging.debug('sign_transaction - Error deserializing transaction context')
            return {"status": 500, "error": "Error deserializing transaction context"}
        secKeys = []
        for key in privateKeys:
            seckey = skycoin.cipher_SecKey()
            error = skycoin.SKY_cipher_SecKeyFromHex(key.encode(), seckey)
            if error != 0:
                logging.debug('sign_transaction - Error parsing hex sec key')
                return {"status": 500, "error": "Error parsing hex sec key"}
            secKeys.append(seckey)
        #This function name changed to SKY_coin_Transaction_GetInputsCount
        error, inputsCount = skycoin.SKY_coin_Transaction_GetInputsCount(transaction_handle)
        if error != 0:
            logging.debug('SKY_coin_Transaction_GetInputsCount failed')
            return {"status": 500, "error": "SKY_coin_Transaction_GetInputsCount failed"}
        #assert len(secKeys) == inputsCount, "seckeys: {} inputs:{}".format(len(secKeys), inputsCount)
        #Match private keys with inputs
        #Transaction was created with more inputs than private secKeys
        #We hope to solve it repeating the first private key
        while len(secKeys) < inputsCount:
            secKeys.append(secKeys[0])
        error = skycoin.SKY_coin_Transaction_SignInputs(transaction_handle, secKeys)
        if error != 0:
            logging.debug('sign_transaction - Error signing transaction')
            return {"status": 500, "error": "Error signing transaction"}
        error, serialized = skycoin.SKY_coin_Transaction_Serialize(transaction_handle)
        if error != 0:
            logging.debug('sign_transaction - Error serializing transaction')
            return {"status": 500, "error": "Error serializing transaction"}
        newContext = str(codecs.encode(serialized, 'hex'))
        if newContext.startswith("b\'"):
            newContext = newContext[2:len(newContext)-1]
        return {"signedTransaction" : newContext}
    except Exception as e:
        logging.debug("Error signing transaction. Error: {}".format(str(e)))
        return {"status": 500, "error": "Unknown Error"}
    finally:
        if transaction_handle != 0:
            skycoin.SKY_handle_close(transaction_handle)
