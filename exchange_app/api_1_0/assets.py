from flask import request, jsonify, make_response
from . import api
from .blockchain import get_url
from ..common import build_error
from ..settings import app_config


@api.route('/assets/<string:assetid>', methods=['GET'])
def get_asset(assetid):
    """
    Retrieve fiber coin asset details.
    """
    if assetid == app_config.SKYCOIN_FIBER_ASSET:
        response_data = {
            "assetId": app_config.SKYCOIN_FIBER_ASSET,
            "address": "",
            "name": app_config.SKYCOIN_FIBER_NAME,
            "accuracy": "6"
        }
        return jsonify(response_data)

    return make_response(jsonify(build_error("Specified asset not found")), 204)


@api.route('/assets', methods=['GET'])
def get_assets_list():
    """
    Return asset list with details of configured Skycoin fiber asset.
    """
    take = 0
    stake = request.args.get('take')
    if stake is None:
        take = app_config.DEFAULT_LIST_LENGTH
    else:
        try:
            take = int(stake)
        except:
            return make_response(jsonify(build_error("Invalid format : take"),
                400))
    cont = request.args.get('continuation')
    if take <= 0 or cont not in (None, "") :
        response_data = {
            "continuation" : "",
            "items": []
        }
    else:
        response_data = {
            "continuation" : "",
            "items": [
                {
                    "assetId": app_config.SKYCOIN_FIBER_ASSET,
                    "address": "",
                    "name": app_config.SKYCOIN_FIBER_NAME,
                    "accuracy": "6"
                }
            ]
        }
    return jsonify(response_data)
