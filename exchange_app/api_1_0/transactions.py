import logging
from flask import jsonify, request, make_response

from . import api
from .blockchain import get_unconfirmed_txs, get_tx_info, get_raw_tx, inject_raw_tx, get_tx_address_related, resend_unconfirmed_txs
from .. import app
from .common import build_error


@api.route('/transactions/unconfirmed', methods=['GET'])
def transactions_unconfirmed():
    result = get_unconfirmed_txs()
    if app.config['DEBUG']:
        logging.debug("Unconfirmed Transactions")
        logging.debug(len(result))
    return jsonify(result)


@api.route('/transaction/info/<string:txid>', methods=['GET'])
def transactions_info(txid):
    result = get_tx_info(txid)
    if app.config['DEBUG']:
        logging.debug("Transaction Info")
        logging.debug(result)
    return jsonify(result)


@api.route('/transaction/raw/<string:txid>', methods=['GET'])
def transaction_raw(txid):
    result = get_raw_tx(txid)
    if app.config['DEBUG']:
        logging.debug("Transaction Info")
        logging.debug(result)
    return jsonify(result)


@api.route('/transaction/inject', methods=['POST'])
def inject_raw_transaction():
    if not request.json:
        return make_response(jsonify(build_error("Input format error")), 400)
    if "rawtx" not in request.json:
        return make_response(jsonify(build_error("Input data error")), 400)
    result = inject_raw_tx(request.json)
    if result['status'] != 200 or result['error'] != "":
        return make_response(
            jsonify(build_error(result['error'])),
            result['status']
        )
    return jsonify(result)


@api.route(
    '/transaction/address-related/<string:addrs>/<int:confirmed>',
    methods=['GET']
)
def transactions_address_related(addrs, confirmed):
    values = {'addrs': addrs, 'confirmed': confirmed}
    result = get_tx_address_related(values)
    return jsonify(result)


@api.route('/transactions/resend', methods=['GET'])
def transactions_resend():
    result = resend_unconfirmed_txs()
    return jsonify(result)
