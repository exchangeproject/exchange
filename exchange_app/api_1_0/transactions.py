import logging
from flask import request, jsonify, make_response

from . import api
from .blockchain import transaction_many_inputs
from .common import build_error
from ..models import add_many_inputs_tx
from .. import app


@api.route('/api/transactions/many-inputs', methods=['POST'])
def transactions_many_inputs():
    if not request.json:
        return make_response(jsonify(build_error("Input format error")), 400)
    params = {'operationId', 'inputs', 'toAddress', 'assetId'}
    if all(x not in params for x in request.json):
        return make_response(jsonify(build_error("Input data error")), 400)
    tx = add_many_inputs_tx(request.json)
    if tx:
        result = transaction_many_inputs(request.json)
        if "transactionContext" in result:
            return jsonify(result)
        if app.config['DEBUG']:
            logging.debug("Transaction: %s", request.args.get('operationId'))
    return jsonify({"status": 500, "error": "Invalid response"})
