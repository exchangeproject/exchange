import logging
from flask import request, jsonify, make_response
from . import api
from .. import app
from ..validate import validate_transaction_broadcast
from ..models import get_transaction, set_transaction_as_broadcasted
from .blockchain import transaction_broadcast
from ..common import build_error

@api.route('/transactions/broadcast', methods=['POST'])
def transactions_broadcast():
    """
    Broadcast transaction
    """
    logging.debug("Broadcasting transaction")
    ok, errormsg = validate_transaction_broadcast(request.json)
    if not ok:
        logging.debug("Invalid transaction to broadcast")
        return make_response(jsonify(build_error(errormsg)), 400)
    operationId = request.json["operationId"]
    tx = get_transaction(operationId)
    if not tx:
        #TODO: We could broadcast the transaction anyway
        logging.debug("Operation Id doesn\'t match a transaction : {}".format(operationId))
        return make_response(jsonify(build_error("Operation Id doesn\'t match a transaction")), 400)
    if 'broadcasted' in tx and tx['broadcasted']:
        logging.debug("Transaction already broadcasted: {}".format(request.json["operationId"]))
        return make_response(jsonify(build_error("Transaction already broadcasted")), 409)
    signedTransaction = request.json['signedTransaction']
    result = transaction_broadcast(signedTransaction)
    if 'error' in result:
        logging.debug("Error broadcasting transaction. Error: {}".format(result['error']))
        return make_response(jsonify(build_error(result['error'])), 400)
    set_transaction_as_broadcasted(tx['_id'])
    return jsonify(result)
