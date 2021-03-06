from flask import request, jsonify, make_response
from . import api
from ..common import build_error
from create_wallet import create_wallet

@api.route('/wallets', methods=['POST'])
def wallets():
    """
    """

    result = create_wallet()

    if "publicAddress" in result:
        return jsonify(result)

    return make_response(
        jsonify(build_error(result["error"])),
        result["status"]
    )


