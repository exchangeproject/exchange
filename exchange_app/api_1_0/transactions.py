import logging
from flask import request, jsonify, make_response

from . import api
from .blockchain import create_transaction
from ..common import build_error
from ..models import add_transaction, get_transaction
from .. import app
from ..validate import validate_transaction_single, validate_transaction_many_outputs

PICK_OUTPUTS=False

@api.route('/transactions/single', methods=['POST'])
def transactions_single():
    tx, errormsg = validate_transaction_single(request.json)
    if not tx:
        return make_response(jsonify(build_error(errormsg)), 400)
    logging.debug('/api/transactions/single')
    savedtx = get_transaction(tx['operationId'])
    transaction_context = False
    if savedtx:
        if 'broadcasted' in savedtx and savedtx['broadcasted']:
            logging.debug('/api/transactions/single - Transaction already broadcasted')
            return make_response("Conflict. Transaction already broadcasted", 409)
        else:
            if 'encoded_transaction' in savedtx:
                logging.debug("Transaction {} already in db".format(tx['operationId']))
                transaction_context = savedtx['encoded_transaction']
    if not transaction_context:
        minhours = 0
        if PICK_OUTPUTS:
            minhours = 4
        result = create_transaction(tx, minhours)
        if 'error' in result:
            status = result.get('status', 500)
            return make_response(result['error'], status)
        transaction_context = str(result['encoded_transaction'])
        if transaction_context.startswith("b\'"):
            transaction_context = transaction_context[2:len(transaction_context)-1]
        add_transaction(tx['operationId'], transaction_context)
    return jsonify({"transactionContext" : transaction_context})

@api.route('/transactions/many-outputs', methods=['POST'])
def transactions_many_outputs():
    tx, errormsg = validate_transaction_many_outputs(request.json)
    if not tx:
        logging.debug('/api/transactions/many-outputs - Error: {}'.format(errormsg))
        return make_response(jsonify(build_error(errormsg)), 400)
    logging.debug('/api/transactions/many-outputs')
    savedtx = get_transaction(tx['operationId'])
    transaction_context = False
    if savedtx:
        if 'broadcasted' in savedtx and savedtx['broadcasted']:
            logging.debug('/api/transactions/many-outputs - Transaction already broadcasted')
            return make_response("Conflict. Transaction already broadcasted", 409)
        else:
            if 'encoded_transaction' in savedtx:
                logging.debug("Transaction {} already in db".format(tx['operationId']))
                transaction_context = savedtx['encoded_transaction']
    if not transaction_context:
        minhours = 0
        if PICK_OUTPUTS:
            minhours = 8
        result = create_transaction(tx, minhours)
        if 'error' in result:
            status = result.get('status', 500)
            return make_response(result['error'], status)
        transaction_context = str(result['encoded_transaction'])
        if transaction_context.startswith("b\'"):
            transaction_context = transaction_context[2:len(transaction_context)-1]
        add_transaction(tx['operationId'], transaction_context)
    return jsonify({"transactionContext" : transaction_context})
