from flask import jsonify, request, make_response
from ..common import api, build_error, error_codes, get_transaction_from_context
from .sign_transaction import sign_transaction

@api.route('/sign', methods=['POST'])
def post_sign():
    """
    Sign transaction with private key
    """
    if not request.json:
        logging.debug('/api/sign - No json data')
        return make_response(jsonify(build_error('Invalid Input Format', error_codes.badFormat)), 400)
    if "privateKeys" not in request.json:
        logging.debug('/api/sign - Missing parameters')
        return make_response(jsonify(build_error('Invalid Input Parameters', error_codes.missingParameter)), 400)
    if "transactionContext" not in request.json:
        logging.debug('/api/sign - Missing parameters')
        return make_response(jsonify(build_error('Invalid Input Parameters', error_codes.missingParameter)), 400)

	#Private keys are ignore because they are inside wallet (which should be encrypted
    private_keys = request.json['privateKeys']
    transactionContext = request.json['transactionContext']
    result = sign_transaction(transactionContext, private_keys)
    if 'error' in result:
        return make_response(jsonify(build_error(result['error'], error_codes.unknown)), result['status'])
    return jsonify(result)
