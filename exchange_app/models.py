import logging
from exchange_app import mongo, app
from bson.objectid import ObjectId
from .api_1_0.blockchain import get_block_count, get_block_range, get_block_by_hash, get_block_by_seq
import requests

def add_address_observation(address):
    """
    Add the specified address to balances observation list and return the mongo document id
    """
    
    collection = mongo.db.observation  #this colection will store all wallets addresses for balance observation
    
    #If address not observed, insert it
    if not exists_address_observation(address):
        id = collection.insert({'address':address})
        if isinstance(id, ObjectId):
            update_index(address)   # Scan the blockchain for the address and update index
            return str(id)
        else:
            return {"status": 500, "error": "Unknown server error"}
    else:
        return {"status" : 409, "error": "Specified address is already observed"} 

    
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
           
        #Remove from index also
        collection = mongo.db.observed_index
        collection.remove({'address': address})
            
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
        

def update_index(new_addr = ''):
    """
    Update the index keeping observation addresses and blocks in which they are referred
    If new_addr is specified, scan from start and update index for the address
    """

    #Get the latest block procesed in index (block height of blockchain in last update)
    collection = mongo.db.observed_index  #this colection will store the index for addresses in observation list
    
    result = collection.find_one({'meta':'blockheight'})
    
    if result is None: #index not created yet
        collection.insert({'meta':'blockheight', 'blockheight': 0})
        collection.insert({'meta':'unspent', 'unspent_outputs': {}})        
        start_block = 1
    else:
        start_block = result['blockheight'] + 1
        
    if new_addr != '': #If new_addr is specified scan from the start to last index blockheight
        start_block = 1
        block_count = result['blockheight']
    else:
        #Get current blockchain blockheight
        block_count = get_block_count()
    
    
    if start_block > block_count: #No new blocks since last update
        return
        
        
    #Get blocks from indexed + 1 to end
    blocks = get_block_range(start_block, block_count) #TODO:implement paging to read blocks
    
    if 'error' in blocks:
        return blocks
    
    
    #Process unindexed blocks. Search for observed adresses and add block# to index
    unspent_outputs = collection.find_one({'meta':'unspent'})
    if unspent_outputs is None:
        unspent_outputs = {}
    else:
        unspent_outputs = unspent_outputs['unspent_outputs']
    
    addresses = []
    if new_addr == '': #If new_addr is specified only search for new_addr
        addresses = get_addresses_balance_observation()
    else:
        addresses.append(new_addr)
    
    for block in blocks:   #Scan the block range
        
        blocknum = block['header']['seq']
        indexed_addresses = [] #Already indexed addresses in this block. Used to not repeat block entry in index if already indexed
        
        for txn in block['body']['txns']:
            
            inputs = txn['inputs']
            outputs = txn['outputs']            
            
            #Outgoing
            for input in inputs:
                if input in unspent_outputs: #Observed address is spending an output
                    uotpt = unspent_outputs.pop(input)
                    addr = uotpt['address']
                    spent_balance = uotpt['balance']
                    
                    #update the balance of address in index
                    collection.update({'address': addr}, {'$inc':{'balance': -spent_balance}}, upsert = True)
                    
                    #Add this blocknum to index for addr
                    if not addr in indexed_addresses:  # Make sure the blocknum is added only once to addr index
                        collection.update({'address': addr}, {'$push':{'blocks': blocknum}}, upsert = True)
                        indexed_addresses.append(addr)
                    
            #Incoming
            for output in outputs:
                addr = output['dst']
                hash = output['uxid']
                received_balance = float(output['coins'])
                
                #Store hash/address mapping
                add_input_mapping(hash, addr, received_balance)
                
                if addr in addresses: #Observed address is receiving a transaction                    
                    
                    collection.update({'address': addr}, {'$inc':{'balance': received_balance}}, upsert = True) #update the balance of address in index
                    unspent_outputs[hash] = {'address': addr, 'balance': received_balance} # save unspent data for later use
                    
                    
                    #Add this blocknum to index for addr
                    if not addr in indexed_addresses:
                        collection.update({'address': addr}, {'$push':{'blocks': blocknum}}, upsert = True)
                        indexed_addresses.append(addr)
                        
        

    #Add remaining unspent outputs to address index
    collection.update({'meta':'unspent'}, {"$set": {'unspent_outputs': unspent_outputs}})
    
    #Update blockheight
    collection.update({'meta':'blockheight'}, {"$set": {'blockheight': block_count}})

    
def get_indexed_balance(address):
    """
    Returns the balance stored in index for the specified address
    """
    
    collection = mongo.db.observed_index  #this colection will store the index for addresses in observation list
    
    result = collection.find_one({'address': address})
    
    if result is None: #index not created yet
        return {"status": 500, "error": "Address is not indexed"}
        
    return {'address': address, 'balance': result['balance']}
    

def get_indexed_blockheight():
    """
    Returns the block height of the blockchain from index
    """
    
    collection = mongo.db.observed_index  #this colection will store the index for addresses in observation list
    
    result = collection.find_one({'meta':'blockheight'})
    
    if result is None: #index not created yet
        return {"status": 500, "error": "Index not created"}
        
    return {'blockheight': result['blockheight']}
    
    
def add_input_mapping(input_hash, address, balance):
    """
    Adds an entry to input hash mapping table
    """
    
    collection = mongo.db.input_mapping  #this colection will store the mapping of inputs to their address
    
    collection.insert({'input_hash': input_hash, 'address': address, 'balance': balance})
    
    
def get_hash_address(input_hash):
    """
    Adds an entry to input hash mapping table
    """
    
    collection = mongo.db.input_mapping  #this colection will store the mapping of inputs to their address
    
    result = collection.find_one({'input_hash': input_hash})
    
    if result is None: #index not created yet
        return {"status": 500, "error": "Index not created"}
        
    return {'address': result['address'], 'balance': result['balance']}
    
        
def get_transactions_from(address, afterhash = ''):
    """
    return all transactions from address after the one specified by afterhash
    """
    
    #Convert afterhash to block sequence number
    if afterhash == '':
        seqno = 1
    else:
        blk = get_block_by_hash(afterhash)
        if 'error' in blk:
            return blk
            
        seqno = blk['header']['seq']
    
    # Get the blocks containing address higher than seqno
    
    collection = mongo.db.observed_index  #this colection will store the index for addresses in observation list
    
    result = collection.find_one({'address': address})
    
    if result is None: #index not created yet
        return {"status": 500, "error": "Address is not indexed"}
        
    mentioned_blocks = result['blocks']
    
    blocks = []  #Holds the mentioned blocks higher than seqno
    
    items = []   # Hold the history output items from specified address
    
    for blockseq in mentioned_blocks:
        if blockseq <= seqno:
            continue
            
        #Read the block from blockchain
        block = get_block_by_seq(blockseq)
        if 'error' in block:
            return block
        
        timestamp = block['header']['timestamp']  #TODO: Convert to ISO 8601 UTC  (Eg: "20071103T161805Z")
        
        for txn in block['body']['txns']:
            inputs = txn['inputs']
            outputs = txn['outputs']   

            operation_id = txn['txid']
            tx_hash = txn['inner_hash']
            
            
            
            #Outgoing
            for input in inputs:
                addr = get_hash_address(input)['address']
                if addr == address: # This is a transaction from specified address    
                    
                    for output in outputs: # Read destination addresses
                        dst_addr = output['dst']
                        if dst_addr != addr:  #Only record if dst is different from self. #TODO: Handle multiple outputs
                            #Record to history output
                            item = {}
                            item['operationId'] =  operation_id
                            item['timestamp'] = timestamp
                            item['fromAddress'] = address
                            item['toAddress'] = dst_addr
                            item['assetId'] = 'SKY'
                            item['amount'] = output['coins']
                            item['hash'] = tx_hash                            
                            items.append(item)
                            
    return items    
    
    
def get_transactions_to(address, afterhash):
    """
    return all transactions to address after the one specified by afterhash
    """
    
    #Convert afterhash to block sequence number
    if afterhash == '':
        seqno = 1
    else:
        blk = get_block_by_hash(afterhash)
        if 'error' in blk:
            return blk
            
        seqno = blk['header']['seq']
    
    # Get the blocks containing address higher than seqno
    
    collection = mongo.db.observed_index  #this colection will store the index for addresses in observation list
    
    result = collection.find_one({'address': address})
    
    if result is None: #index not created yet
        return {"status": 500, "error": "Address is not indexed"}
        
    mentioned_blocks = result['blocks']
    
    blocks = []  #Holds the mentioned blocks higher than seqno
    
    items = []   # Hold the history output items from specified address
    
    for blockseq in mentioned_blocks:
        if blockseq <= seqno:
            continue
            
        #Read the block from blockchain
        block = get_block_by_seq(blockseq)
        if 'error' in block:
            return block
        
        timestamp = block['header']['timestamp']  #TODO: Convert to ISO 8601 UTC  (Eg: "20071103T161805Z")
        
        for txn in block['body']['txns']:
            inputs = txn['inputs']
            outputs = txn['outputs']   

            operation_id = txn['txid']
            tx_hash = txn['inner_hash']
            
            orig_addr = get_hash_address(inputs[0])['address']
            
            for output in outputs: # Read destination addresses
                if output['dst'] == address and orig_addr != address:  
                    #Record to history output
                    item = {}
                    item['operationId'] =  operation_id
                    item['timestamp'] = timestamp
                    item['fromAddress'] = orig_addr  #TODO: Handle multiple inputs
                    item['toAddress'] = address
                    item['assetId'] = 'SKY'
                    item['amount'] = output['coins']
                    item['hash'] = tx_hash                            
                    items.append(item)
                            
    return items    
    