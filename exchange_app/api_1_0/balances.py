from flask import request, jsonify, make_response
from . import api
from .common import build_error, generate_hash_key
from ..models import add_address_observation, delete_address_observation, get_addresses_balance_observation, update_index, get_indexed_balance, get_indexed_blockheight
from .redis_interface import get_cont_address_balances, set_cont_address_balances, del_cont_address_balances
import logging
from .. import app
from .blockchain import get_balance, get_balance_scan
from time import perf_counter


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
    Get balances of addresses in observation list
    """

    perf = perf_counter()
    update_index()
    logging.debug("index check perf : {0:.3f}".format( perf_counter() - perf ))
    
    
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
    
    items = []
    
    #define search boundaries
    start_index = 0 if cont_address == "" or cont_address not in addresses else addresses.index(cont_address)
    total_items = take if take != 0 else len(addresses)   
    
    blockheight = get_indexed_blockheight()
    if 'error' in blockheight:
        return make_response(jsonify(build_error(blockheight["error"])), blockheight["status"])

    while len(items) < total_items and start_index < len(addresses):
        item = {}
        
        #Get balance from index
        #balance = get_indexed_balance(addresses[start_index])        
        balance = get_indexed_balance(addresses[start_index])        
        if 'error' in balance: #If there is an error in balance, continue with the next address
            start_index += 1
            continue
     
        #Generate output response
        item['address'] = addresses[start_index]
        item['assetId'] = 'SKY'
        item['balance'] = str(balance['balance'])  #TODO: Asset accuracy
        #TODO: Handle case when address is deleted during paging read
        item['block'] = blockheight
        if balance['balance'] != 0:
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
        

    return jsonify(response)
