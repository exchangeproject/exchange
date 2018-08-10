import logging
from flask import request, jsonify, make_response

from . import api
from .blockchain import check_balance_from_transaction
from ..common import build_error, get_transaction_context
from ..models import add_transaction
from .. import app
from ..validate import validate_transaction_single

@api.route('/transactions/single', methods=['POST'])
def transactions_single():
    tx, errormsg = validate_transaction_single(request.json)
    if not tx:
        return make_response(jsonify(build_error(errormsg)), 400)
    balance_ok, errorcode, errormsgg = check_balance_from_transaction(tx)
    if not balance_ok:
        return make_response(errormsg, errorcode)
    logging.debug('/api/transactions/single - Transaction: ' + jsonify(tx))
    tx = add_transaction(tx)
    if not tx:
        logging.debug('/api/transactions/single - Error while adding transaction')
        return make_response("Unknown server error", 500)
    elif tx['broadcasted']:
        logging.debug('/api/transactions/single - Transaction already broadcasted')
        return make_response("Conflict. Transaction already broadcasted", 409)

    transaction_context = get_transaction_context(tx)
    return jsonify({"transactionContext" : transaction_context})

@api.route('/transactions/many-outputs', methods=['POST'])
def transactions_many_outputs():
    tx, errormsg = validate_transaction_many_outputs(request.json)
    if not tx:
        return make_response(jsonify(build_error(errormsg)), 400)
    balance_ok, errorcode, errormsgg = check_balance_from_transaction(tx)
    if not balance_ok:
        return make_response(errormsg, errorcode)
    logging.debug('/api/transactions/many-outputs - Transaction: ' + jsonify(tx))
    tx = add_transaction(tx)
    if not tx:
        logging.debug('/api/transactions/many-outputs - Error while adding transaction')
        return make_response("Unknown server error", 500)
    elif tx['broadcasted']:
        logging.debug('/api/transactions/many-outputs - Transaction already broadcasted')
        return make_response("Conflict. Transaction already broadcasted", 409)

    transaction_context = get_transaction_context(tx)
    return jsonify({"transactionContext" : transaction_context})

'''
@api.route('/api/transactions/many-inputs', methods=['POST'])
def transactions_many_inputs():
    if not request.json:
        return make_response(jsonify(build_error("Input format error")), 400)
    params = {'operationID', 'inputs', 'toAddress', 'assetId'}
    if all(x not in params for x in request.json):
        return make_response(jsonify(build_error("Input data error")), 400)
    result = transaction_many_inputs(request.json)
    if "transactionContext" in result:
        return jsonify(result)
    return jsonify({"status": 500, "error": "Invalid response"})


@api.route('/api/transactions/many-outputs', methods=['POST'])
def transactions_many_outputs():
    if not request.json:
        return make_response(jsonify(build_error("Input format error")), 400)
    params = {'operationId', 'fromAddress', 'fromAddressContext', 'outputs', 'assetId'}
    if all(x not in params for x in request.json):
        return make_response(jsonify(build_error("Input data error")), 400)
    tx = add_many_outputs_tx(request.json)
    if tx:
        result = transaction_many_outputs(request.json)
        if "transactionContext" in result:
            return jsonify(result)
        if app.config['DEBUG']:
            logging.debug("Transaction: %s", request.args.get('operationId'))
    return jsonify({"status": 500, "error": "Invalid response"})
'''
