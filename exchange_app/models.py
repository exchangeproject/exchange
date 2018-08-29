import logging
from exchange_app import mongo, app
from bson.objectid import ObjectId
from .api_1_0.blockchain import get_block_count, get_block_range, get_block_by_hash, get_block_by_seq, get_address_transactions
import requests
from datetime import  datetime, timezone
from time import perf_counter
import base64

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

        #Remove address from index if not exists in other observation lists.

        if not exists_address_transfer_observation_from(address) and not exists_address_transfer_observation_to(address):
            remove_from_index(address)

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
        timestamp = int(datetime.utcnow().timestamp())
        logging.debug("Adding address to observation: {}, time: {}".\
            format(address, timestamp))
        id = collection.insert({'address':address,
            'timestamp':timestamp})

        if isinstance(id, ObjectId):
            update_index(address)
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
        timestamp = int(datetime.utcnow().timestamp())
        logging.debug("Adding address to observation: {}, time: {}".\
            format(address, timestamp))
        id = collection.insert({'address':address,
            'timestamp': timestamp})

        if isinstance(id, ObjectId):
            update_index(address)
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

        #Remove address from index if not exists in other observation lists.

        if not exists_address_transfer_observation_to(address) and not exists_address_observation(address):
            remove_from_index(address)

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

        #Remove address from index if not exists in other observation lists.

        if not exists_address_transfer_observation_from(address) and not exists_address_observation(address):
            remove_from_index(address)

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
        if collection.find_one({'address': new_addr}) is not None:   #address already indexed
            logging.debug("update_index: address: {} already indexed".format(new_addr))
            return {}

        start_block = 1
        block_count = result['blockheight']
    else:
        #Get current blockchain blockheight
        block_count = get_block_count()


    if start_block > block_count: #No new blocks since last update
        logging.debug("update_index: no new block since last update. " + \
            "start block: {} block count: {}".format(start_block, block_count))
        return {}

    #Process unindexed blocks. Search for observed adresses and add block# to index
    unspent_outputs = collection.find_one({'meta':'unspent'})
    if unspent_outputs is None:
        unspent_outputs = {}
    else:
        unspent_outputs = unspent_outputs['unspent_outputs']

    addresses = []
    if new_addr == '': #If new_addr is specified only search for new_addr
        addresses = list(set(get_addresses_balance_observation() + get_addresses_transfers_observation_from() + get_addresses_transfers_observation_to()))
    else:
        addresses.append(new_addr)

    logging.debug("update_index: Scanning blocks {} - {} for addresses: {}" \
            .format(start_block, block_count, addresses))
    #Get blocks from indexed + 1 to end in batches of 100
    step = 100   #How many blocks to retrieve in one batch
    for bn in range(start_block, block_count + 1, step):
        logging.debug("update_index: Scanning blocks: {} - {}" \
            .format(bn, bn + step - 1))
        blocks = get_block_range(bn, bn + step - 1)
        if 'error' in blocks:
            return blocks

        for block in blocks:   #Scan the block range

            blocknum = block['header']['seq']

            indexed_addresses = [] #Already indexed addresses in this block. Used to not repeat block entry in index if address already indexed

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



def remove_from_index(address):
    """
    Remove address from index
    """
    collection = mongo.db.observed_index
    collection.remove({'address': address})



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


def get_transactions_from(address, take, afterhash = ''):
    """
    return all transactions from address after the one specified by afterhash
    """

    # Get the blocks mentioning address
    collection = mongo.db.observed_index  #this colection will store the index for addresses in observation list
    result = collection.find_one({'address': address})

    if result is None: #index not created yet
        return {"status": 500, "error": "Address is not indexed"}

    collection = mongo.db.trans_obs_from #colection of observed addresses
    ob_address = collection.find_one({'address': address})
    if ob_address is None: #Address not in observation list
        return {"status": 500, "error": "Address is not in observation list"}

    mentioned_blocks = result['blocks']
    logging.debug("Searching transactions in blocks: {}".format(mentioned_blocks))

    items = []   # Hold the history output items from specified address
    process_txn = False
    taken = 0
    finish = False

    for blockseq in mentioned_blocks:

        #Read the block from blockchain
        block = get_block_by_seq(blockseq)
        if 'error' in block:
            return block

        timestamp = block['header']['timestamp']
        if timestamp < ob_address['timestamp']:
            logging.debug("Transaction out of time: {}".format(timestamp))
            continue
        timestamp = datetime.fromtimestamp(timestamp, timezone.utc).isoformat()

        for txn in block['body']['txns']:
            logging.debug("Transaction hash: {}".format(txn['inner_hash']))
            tx_hash = _hexToB64(txn['inner_hash'])
            #If afterhash is specified, return from that point only
            if afterhash == '' or tx_hash == afterhash:
                process_txn = True

            if not process_txn:
                continue

            inputs = txn['inputs']
            outputs = txn['outputs']
            txn_type = txn['type']

            #Outgoing

            input_addresses = []

            if len(inputs) == 0:
                logging.debug("No inputs")

            for input in inputs:
                logging.debug("Checking input: {}".format(input))
                addr = get_hash_address(input)['address']
                logging.debug("Address from input: {}".format(addr))

                if addr not in input_addresses: # count multiple inputs hashes from same address as one
                    input_addresses.append(addr)
                else:
                    continue

                if addr == address: # This is a transaction from specified address

                    for output in outputs: # Read destination addresses
                        dst_addr = output['dst']
                        if dst_addr != addr:  #Only record if dst is different from self. #TODO: Handle multiple outputs
                            #Record to history output
                            item = {}
                            #item['transactionType'] =  txn_type
                            item['timestamp'] = timestamp
                            item['fromAddress'] = address
                            item['toAddress'] = dst_addr
                            item['assetId'] = 'SKY'
                            item['amount'] = output['coins']
                            item['hash'] = tx_hash
                            items.append(item)
                            taken += 1
                            if taken >= take:
                                return items

    return items


def get_transactions_to(address, take, afterhash = ''):
    """
    return 'take' transactions to address after the one specified by afterhash
    """

    collection = mongo.db.trans_obs_to  #this colection will store the addresses in observation list

    result = collection.find_one({'address': address})

    if result is None: #index not created yet
        return {"status": 500, "error": "Address is not observed"}

    collection = mongo.db.trans_obs_to #colection of observed addresses
    ob_address = collection.find_one({'address': address})
    if ob_address is None: #Address not in observation list
        return {"status": 500, "error": "Address is not in observation list"}

    txns = get_address_transactions(address)

    items = []   # Hold the history output items from specified address
    process_txn = False
    taken = 0

    for txn in txns:

        tx_hash = txn['txn']['inner_hash']
        tx_hash = _hexToB64(tx_hash)


        #If afterhash is specified, return from that point only
        if afterhash == '' or tx_hash == afterhash:
            process_txn = True

        if not process_txn:
            continue



        timestamp = txn['time']
        if timestamp < ob_address['timestamp']:
            logging.debug("Transaction out of time: {}".format(timestamp))
            continue
        timestamp = datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
        txn_type = txn['txn']['type']
        orig_addr = get_hash_address(txn['txn']['inputs'][0])['address']

        for output in txn['txn']['outputs']: # Read destination addresses
            if output['dst'] == address and orig_addr != address:
                #Record to history output
                item = {}
                item['timestamp'] =  timestamp
                item['fromAddress'] = orig_addr
                item['toAddress'] = address  #TODO: Handle multiple inputs
                item['assetId'] = 'SKY'
                item['amount'] = output['coins']
                item['hash'] = tx_hash
                #item['transactionType'] = txn_type
                items.append(item)
                taken += 1
                if taken >= take:
                    return items

    return items

def add_transaction(operationId, encodedTransaction):
    """
    Add a transaction to db
    """
    transactions = mongo.db.transactions #Collection to store transactions
    tx = {
        'operationId' : operationId,
        'encoded_transaction' : encodedTransaction,
        'broadcasted' : False
    }
    pk = transactions.insert(tx)
    if isinstance(pk, ObjectId):
        return tx
    return False

def get_transaction(operationId):
    """
    Find transaction by operation id
    """
    transactions = mongo.db.transactions #Collection to store transactions
    result = transactions.find_one({'operationId' : operationId})
    if result:
        return result
    return False

def set_transaction_as_broadcasted(id):
    """
    Sets the given transaction as broadcasted
    """
    transactions = mongo.db.transactions #Collection to store transactions
    transactions.update({'_id': id}, {'$set': {'broadcasted': True}})

def _hexToB64(s):
    r = base64.b64encode(bytes.fromhex(s))
    r = str(r)
    if r.startswith("b\'"):
        r = r[2:len(r)-1]
    return r
