from flask import request, jsonify, make_response
from . import api
from .blockchain import spend, create_wallet
from .common import build_error


@api.route('/wallets', methods=['POST'])
def wallets():
    """
    """

    result = create_wallet()

    if "address" in result:
        return jsonify(result)

    return make_response(
        jsonify(build_error(result["error"])),
        result["status"]
    )


@api.route('/wallets/<string:address>/cashout', methods=['POST'])
def wallets_cashout(address):
    """
    Record transaction in blockchain from wallet address to destination address in json request
    Validate request json
    """

    if not request.json:  # bad request
        return make_response(jsonify(build_error("Input format error")), 400)

    error_items = {}

    if "operationId" not in request.json:
        error_items["operationId"] = ["Missing item"]
    if "to" not in request.json:
        error_items["to"] = ["Missing item"]
    if "assetId" not in request.json:
        error_items["assetId"] = ["Missing item"]
    if "amount" not in request.json:
        error_items["amount"] = ["Missing item"]

    if error_items != {}:  # Bad request
        return make_response(
            jsonify(build_error("Input data error", 400, error_items)),
            400
        )

    values = {}
    values["id"] = address
    values["dst"] = request.json["to"]
    values["coins"] = request.json["amount"]

    # Call blockchain to spend
    result = spend(values)
    print(result)
    if result["status_code"] != 200 or result["error"] != "":
        return make_response(
            jsonify(build_error(result["error"])),
            result["status"]
        )

    return make_response("", 200)
