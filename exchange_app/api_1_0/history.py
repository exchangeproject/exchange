from flask import request, jsonify, make_response
from . import api
from ..common import build_error
from ..models import exists_address_transfer_observation_to, exists_address_transfer_observation_from
from ..models import add_transaction_observation_to_address, add_transaction_observation_from_address
from ..models import delete_transaction_observation_to_address, delete_transaction_observation_from_address
from ..models import get_transactions_from, get_transactions_to, update_index
import logging
from .. import app


@api.route('/transactions/history/from/<string:address>', methods=['GET'])
def get_history_from_address(address):
    """
    Returns completed transactions that transfer fund from the address
    """

    if not exists_address_transfer_observation_from(address):
        return make_response(jsonify(build_error('No content. transactions from the address are not observed')), 204)

    take = request.args.get('take')
    if take is None:
        take = 0
    else:
        take = int(take)

    afterhash = request.args.get('afterHash')
    if afterhash is None:
        afterhash = ""
    logging.debug("Getting history from address: {}".format(address))
    update_index()
    items = get_transactions_from(address, take, afterhash)

    if 'error' in items:
        return make_response(jsonify(build_error(items['error'])), items['status'])

    return jsonify(items)


@api.route('/transactions/history/to/<string:address>', methods=['GET'])
def get_history_to_address(address):
    """
    Returns completed transactions that transfer fund to the address
    """

    if not exists_address_transfer_observation_to(address):
        return make_response(jsonify(build_error('No content: transactions to the address are not observed')), 204)

    take = request.args.get('take')
    if take is None:
        take = 0
    else:
        take = int(take)

    afterhash = request.args.get('afterHash'.lower())
    if afterhash is None:
        afterhash = ''

    update_index()
    items = get_transactions_to(address, take, afterhash)

    response = items if take == 0 else items[0:take]

    return jsonify(response)



@api.route('/transactions/history/from/<string:address>/observation', methods=['DELETE'])
def del_history_from_address(address):
    """
    Stops observation of the transactions that transfer fund from the address
    """

    result = delete_transaction_observation_from_address(address)

    # if successfully deleted from observation list, return a plain 200
    if "error" in result:
        return make_response(jsonify(build_error(result["error"])), result["status"])
    else:
        return ""


@api.route('/transactions/history/to/<string:address>/observation', methods=['DELETE'])
def del_history_to_address(address):
    """
    Stops observation of the transactions that transfer fund to the address
    """

    result = delete_transaction_observation_to_address(address)

    # if successfully deleted from observation list, return a plain 200
    if "error" in result:
        return make_response(jsonify(build_error(result["error"])), result["status"])
    else:
        return ""


@api.route('/transactions/history/from/<string:address>/observation', methods=['POST'])
def add_history_from_address(address):
    """
    Starts observation of the transactions that transfer fund from the address
    """

    result = add_transaction_observation_from_address(address)

    # if successfully stored in observation list, return a plain 200
    if "error" in result:
        return make_response(jsonify(build_error(result["error"])), result["status"])
    else:
        return ""


@api.route('/transactions/history/to/<string:address>/observation', methods=['POST'])
def add_history_to_address(address):
    """
    Starts observation of the transactions that transfer fund from the address
    """

    result = add_transaction_observation_to_address(address)

    # if successfully stored in observation list, return a plain 200
    if "error" in result:
        return make_response(jsonify(build_error(result["error"])), result["status"])
    else:
        return ""
