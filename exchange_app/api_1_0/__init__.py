from flask import Blueprint

api = Blueprint('api', __name__)

from . import address, wallets, assets, pending_events, capabilities, isalive, common, balances, transactions, history
