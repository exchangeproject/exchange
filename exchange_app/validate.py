import logging

def validate_transaction_single(json):
    if not json:
        logging.debug('/api/transactions/single - No json data')
        return False, "Input format error"
    params = {'operationID', 'fromAddress', 'fromAddressContext',
            'toAddress', 'assetId', 'amount', 'includeFee'}
    if all(x not in params for x in json):
        logging.debug('/api/transactions/single - Missing parameters')
        return False, "Input format error"
    try:
        amount = int(json['amount'])
    except:
        logging.debug('/api/transactions/single - Error while parsing amount')
        return False, "Amount is not an integer"
    if amount <= 0:
        logging.debug('/api/transactions/single - Amount is zero')
        return False, "Amount is zero"
    amount = float(amount) / 1000000 #Convert to droplets
    if json['assetId'] != 'SKY':
        logging.debug('/api/transactions/single - Asset id must be SKY')
        return False, "Only coin is SKY"
    tx = {'operationId' : json['operationID'],
            'fromAddress' : json['fromAddress'],
            'fromAddressContext' : json['fromAddressContext'],
            'outputs': [{
                'amount' : amount,
                'toAddress' : json['toAddress']
            }],
            'assetId' : json['assetId'],
            'includeFee' : json['includeFee']}
    return tx, ""

def validate_transaction_many_outputs(json):
    if not json:
        logging.debug('/api/transactions/many-outputs - No json data')
        return False, "No input data."
    if not 'operationID' in json or not 'assetId' in json:
        return False, "Input format error. No operationId"
    if json['assetId'] != 'SKY':
        logging.debug('/api/transactions/many-outputs - Asset id must be SKY')
        return False, "Only coin is SKY"
    if not 'outputs' in json:
        return False, "Input format error. No outputs."
    outputs = json['outputs']
    if not isinstance(outputs, list) or len(outputs) <= 0:
        return False, "Input format error. Outputs should be array."
    tos = []
    for output in outputs:
        if not 'toAddress' in output or not 'amount' in output:
            return False, "Input format error. Invalid outputs"
        amount = 0
        try:
            amount = int(output['amount'])
        except:
            logging.debug('/api/transactions/single - Error while parsing amount')
            return False, "Amount is not an integer"
        if amount <= 0:
            logging.debug('/api/transactions/single - Amount is zero')
            return False, "Amount is zero"
        amount = float(amount) / 1000000 #Convert to droplets
        to = {
            'toAddress' : output['toAddress'],
            'amount' : amount
        }
        tos.append(to)
    tx = {'operationId' : json['operationID'],
            'fromAddress' : json['fromAddress'],
            'fromAddressContext' : json['fromAddressContext'],
            'outputs': tos,
            'assetId' : json['assetId'],
            'includeFee' : False}
    return tx, ""

def validate_sign_transaction(json):
    if not json:
        logging.debug('sign_transaction - No json data')
        return False, "Input format error"
    params = {'operationID', 'fromAddress', 'fromAddressContext',
            'outputs', 'assetId', 'includeFee'}
    if all(x not in params for x in json):
        logging.debug('sign_transaction - Missing parameters')
        return False, "Input format error"
    if json['assetId'] != 'SKY':
        logging.debug('sign_transaction - Asset id must be sky')
        return False, "Only coin is sky"
    return True, ""

def validate_transaction_broadcast(json):
    if not json:
        logging.debug('/api/transactions/broadcast - No json data')
        return False, 'Invalid Input Format'
    if "operationId" not in json:
        logging.debug('/api/transactions/broadcast - Missing parameters')
        return False, 'Invalid Input Parameters'
    if "signedTransaction" not in json:
        logging.debug('/api/transactions/broadcast - Missing parameters')
        return False, 'Invalid Input Parameters'
    return True, ""
