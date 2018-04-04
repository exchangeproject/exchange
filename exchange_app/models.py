import logging
from exchange_app import mongo, app
from bson.objectid import ObjectId

def add_address_observation(address):
    """
    Add the specified address to balances observation list and return the mongo document id
    """
    
    collection = mongo.db.observation  #this colection will store all wallets addresses for balance observation
    
    #If address not observed, insert it
    if not exists_address_observation(address):
        id = collection.insert({'address':address, 'balance': 0, 'block': 1})
        if isinstance(id, ObjectId):
            return str(id)
        else:
            return {"status": 500, "error": "Unknown server error"}
    else:
        return {"status" : 409, "error": "Specified address is already observed"} 


def update_address_observation(address, balance, block):
    """
    Update the balance and block heigh in specified address entry
    """
    collection = mongo.db.observation  #this colection will store all wallets addresses for balance observation
    
    if exists_address_observation(address):
        result = collection.update({'address': address}, {'$set': {'balance': balance, 'block': block}})
        
        if not 'n' in result:
            return {"status": 500, "error": "Unknown server error"}
        if result['n'] == 0:
            return {"status": 500, "error": "Unknown server error"}
            
        return result
    else:
        return {"status" : 204, "error": "Specified address is not observed"} 
    

def get_address_observation_data(address):
    """
    Return the balance and block heigh in specified address entry 
    """
    collection = mongo.db.observation  #this colection will store all wallets addresses for balance observation
        
    #If address already observed, delete it
    if exists_address_observation(address):
        result = collection.find_one({'address':address})
        
        logging.debug(result)
        
        if not '_id' in result:
            return {"status": 500, "error": "Unknown server error"}
        
        return {'address': result['address'], 'balance': result['balance'], 'block': result['block']}
        
    else:
        return {"status" : 204, "error": "Specified address is not observed"} 
    
    
    
    
def delete_address_observation(address):
    """
    delete the specified address from balances observation list
    """
    
    collection = mongo.db.observation  #this colection will store all wallets addresses for balance observation
        
    #If address already observed, delete it
    if exists_address_observation(address):
        result = collection.remove({'address':address})
        
        if not 'n' in result:
            return {"status": 500, "error": "Unknown server error"}
        if result['n'] == 0:
            return {"status": 500, "error": "Unknown server error"}
            
        return result
    else:
        return {"status" : 204, "error": "Specified address is not observed"} 
    
    
    

def get_address_list(collection):
    """
    return addresses in observation list
    """

    result = collection.find()
    
    addresses = []
    
    for addr in result:
        addresses.append(addr['address'])
    
    return addresses
    

def get_addresses_balance_observation():
    """
    return addresses in observation list
    """    
    return get_address_list(mongo.db.observation)
    
def get_addresses_transfers_observation_from():
    """
    return addresses in observation list
    """    
    return get_address_list(mongo.db.trans_obs_from)
    
def get_addresses_transfers_observation_to():
    """
    return addresses in observation list
    """    
    return get_address_list(mongo.db.trans_obs_to)


def exists_address_observation(address):
    """
    return addresses in observation list
    """
    collection = mongo.db.observation
    result = collection.find_one({'address': address})
    if result:
        return True
    else:
        return False

        
def exists_address_transfer_observation_to(address):
    """
    return addresses in observation list
    """
    collection = mongo.db.trans_obs_to
    result = collection.find_one({'address': address})
    if result:
        return True
    else:
        return False
        
def exists_address_transfer_observation_from(address):
    """
    return addresses in observation list
    """
    collection = mongo.db.trans_obs_from
    result = collection.find_one({'address': address})
    if result:
        return True
    else:
        return False
        
        

def add_transaction_observation_from_address(address):
    """
    Add the specified address to transaction observation list to it and return the mongo document id
    """
    
    collection = mongo.db.trans_obs_from  #this colection will store all wallets addresses for transaction observation from it
    
    #If address not observed, insert it
    if not exists_address_transfer_observation_from(address):
        id = collection.insert({'address':address})
        
        if isinstance(id, ObjectId):
            return str(id) 
        else:
            return {"status": 500, "error": "Unknown server error"}
    else:
        return {"status" : 409, "error": "Specified address is already observed"} 

        
def add_transaction_observation_to_address(address):
    """
    Add the specified address to transaction observation list to it and return the mongo document id
    """
    
    collection = mongo.db.trans_obs_to  #this colection will store all wallets addresses for transaction observation from it
    
    #If address not observed, insert it
    if not exists_address_transfer_observation_to(address):
        id = collection.insert({'address':address})
        
        if isinstance(id, ObjectId):
            return str(id) 
        else:
            return {"status": 500, "error": "Unknown server error"}
    else:
        return {"status" : 409, "error": "Specified address is already observed"} 
        

def delete_transaction_observation_from_address(address):
    """
    Add the specified address to observation list and return the mongo document id
    """
    
    collection = mongo.db.trans_obs_from  #this colection will store all wallets addresses for balance observation
        
    #If address already observed, delete it
    if exists_address_transfer_observation_from(address):
        result = collection.remove({'address':address})
        
        if not 'n' in result:
            return {"status": 500, "error": "Unknown server error"}
        if result['n'] == 0:
            return {"status": 500, "error": "Unknown server error"}
            
        return result
    else:
        return {"status" : 204, "error": "Specified address is not observed"} 


def delete_transaction_observation_to_address(address):
    """
    Add the specified address to observation list and return the mongo document id
    """
    
    collection = mongo.db.trans_obs_to  #this colection will store all wallets addresses for balance observation
        
    #If address already observed, delete it
    if exists_address_transfer_observation_to(address):
        result = collection.remove({'address':address})
        
        if not 'n' in result:
            return {"status": 500, "error": "Unknown server error"}
        if result['n'] == 0:
            return {"status": 500, "error": "Unknown server error"}
            
        return result
    else:
        return {"status" : 204, "error": "Specified address is not observed"} 
