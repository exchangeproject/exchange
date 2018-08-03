from flask import Blueprint

api = Blueprint('api', __name__)

from . import address, wallets, assets, pending_events, capabilities, isalive, balances, history, explorer_url, transactions
