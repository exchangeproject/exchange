from flask import request, jsonify, make_response
from . import api
from .common import build_error, generate_hash_key
from ..models import add_address_observation, delete_address_observation, get_addresses_balance_observation
from .redis_interface import get_cont_address_balances, set_cont_address_balances, del_cont_address_balances
import logging
from .. import app
from .blockchain import get_balance


@api.route('/balances/<string:address>/observation', methods=['POST'])
def add_observation(address):
    """
    Add the specified address to observation list
    """

    result = add_address_observation(address)

    # if successfully stored in observation list, return a plain 200
    if "error" in result:
        return make_response(jsonify(build_error(result["error"])), result["status"])
    else:
        return ""


@api.route('/balances/<string:address>/observation', methods=['DELETE'])
def delete_observation(address):
    """
    Delete the specified address from observation list
    """

    result = delete_address_observation(address)

    # if successfully deleted from observation list, return a plain 200
    if "error" in result:
        return make_response(jsonify(build_error(result["error"])), result["status"])
    else:
        return ""
        
    
@api.route('/balances', methods=['GET'])
def get_balances():
    """
    Get balances of address in observation list
    """
    
    take = request.args.get('take')
    if take is None:
        take = 0
    else:
        take = int(take)
    
    continuation = request.args.get('continuation')
    if continuation is None:
        continuation = ""
    
    #get continuation address if continuation context is set
    cont_address = ""
    if continuation != "":
        cont_address = get_cont_address_balances(continuation) #get the continuation address from redis
        
    
    #Get address list from mongodb
    addresses = get_addresses_balance_observation()  

    if app.config['DEBUG']:
        logging.debug("addresses")
        logging.debug(addresses)
    
    items = []
    
    #define search boundaries
    start_index = 0 if cont_address == "" or cont_address not in addresses else addresses.index(cont_address)
    total_items = take if take != 0 else len(addresses)   

    while len(items) < total_items and start_index < len(addresses):
        item = {}
        
        if app.config['DEBUG']:
            logging.debug("Start Index: %i", start_index)
            logging.debug("Total Items: %i", total_items)
            logging.debug("address: %s", addresses[start_index])
            
        item['address'] = addresses[start_index]
        item['assetId'] = 0
        item['balance'] = 4# get_balance(addr) #TODO: uncomment get balances when finish testing. Otherwise nothing will be returned
        #TODO: Handle case when address is deleted during paging read
        item['block'] = 0 #TODO: where to get block sequence?
        if item['balance'] != 0:
            items.append(item)
        start_index += 1

    #Save continuation address in Redis
    if start_index < len(addresses): #Still data to read        
        #If it is the first call and need continuation create the token
        if continuation == "" and take != 0 and take < len(addresses):
            continuation = generate_hash_key()        
        set_cont_address_balances(continuation, addresses[start_index])
    else:
        del_cont_address_balances(continuation)
        continuation = ""

    response = {"continuation": continuation, "items": items}
    
    if app.config['DEBUG']:
        logging.debug("Got balances from observation list")
        logging.debug(items)
        

    return jsonify(response)
