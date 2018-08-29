import unittest
import os
from exchange_app import app
from exchange_app.settings import app_config
import json
import skycoin
import binascii
import urllib.request
import urllib.parse
import time
import logging
import codecs
import ssl
import base64

LIVE_TRANSACTIONS_TEST_SKYCOIN_NODE_URL = "https://skyapi.simelo.tech:6420/"
#LIVE_TRANSACTIONS_TEST_SKYCOIN_NODE_URL = "http://127.0.0.1:6421/"
SYNCHRONIZATION_SERVER = "http://107.173.160.237:8080/"
#SYNCHRONIZATION_SERVER = "http://localhost:8080/"

class LiveTestCase(unittest.TestCase):
    serverUp = False

    def test_transactions(self):
        sourceAddress1, sourceAddress2 = self._pickAddresses()
        sources = [sourceAddress1]
        if sourceAddress2 != sourceAddress1:
            sources.append(sourceAddress2)
        destAddress1 = self._lockAddress()
        destAddress2 = self._lockAddress()

        self._addToBalanceObservations(sources + [destAddress1, destAddress2])
        self._addToHistoryObservations(sources,
            [destAddress1, destAddress2])
        self._checkTransactionSingle(sourceAddress1, destAddress1)
        self._removeFromHistoryObservations(sources,
            [destAddress1, destAddress2])
        self._addToHistoryObservations(sources,
            [destAddress1, destAddress2])
        self._checkTransactionManyOutputs(sourceAddress2,
                destAddress1, destAddress2)
        self._removeFromBalanceObservations(sources + [destAddress1, destAddress2])
        self._removeFromHistoryObservations(sources,
            [destAddress1, destAddress2])
        self._checkNotObservedHistoryFail(sourceAddress1, destAddress1)
        if sourceAddress1 != '':
            self._freeAddress(sourceAddress1)
        if sourceAddress2 != '' and sourceAddress2 != sourceAddress1:
            self._freeAddress(sourceAddress2)
        if destAddress1 != '':
            self._freeAddress(destAddress1)
        if destAddress2 != '':
            self._freeAddress(destAddress2)

    def test_failing_operations(self):
        sourceAddress = self.mainAddress
        mainWallet = self.wallets[self.mainAddress]
        walletName = mainWallet["addressContext"]
        destAddress = self._pickAnyAddress()
        testTx = {
            'operationID' : "22222222",
            'fromAddress' : sourceAddress,
            'fromAddressContext' : walletName,
            'toAddress' : destAddress,
            'assetId' : 'SKY',
            'amount' : 1e15, #Hoping there will never be 1 thousand skys
            'includeFee' : False
        }
        response = self.app.post(
            '/v1/api/transactions/single',
            data = json.dumps(testTx),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 200) #Not enough balance
        testTx['amount'] = 1 #amount to small
        response = self.app.post(
            '/v1/api/transactions/single',
            data = json.dumps(testTx),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 200) #amount to small
        testTx = {
            'operationID' : "22222222"
        }
        response = self.app.post(
            '/v1/api/transactions/single',
            data = json.dumps(testTx),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400) #Missing parameters

    def setUp(self):
        logging.debug("setup started")
        ssl._create_default_https_context = ssl._create_unverified_context
        self.defaultSkycoinNodeUrl = app_config.SKYCOIN_NODE_URL
        app_config.SKYCOIN_NODE_URL = LIVE_TRANSACTIONS_TEST_SKYCOIN_NODE_URL
        self.app = app.test_client()
        self.mainAddress = "2JvBi6BgCsZAzvbhCna4WTfD4FATCPwp2f1"
        self._getCSRFToken()
        self.wallets = self._getTestWallets()
        self._recreateWalletAddresses()
        self.lockedAddresses = {}

    def tearDown(self):
        for address in self.lockedAddresses.keys():
            if self.lockedAddresses[address]:
                self._freeAddress(address)
        balance = self._getBalanceForAddresses([self.mainAddress])
        logging.debug("Balance at tearDown: {}".format(balance))

    def _getBalanceForAddresses(self, addresses):
        logging.debug("Calling skycoin to get balances")
        data = {"addrs": ",".join(addresses)}
        data = urllib.parse.urlencode(data)
        balances = self.makeHttpRequest("api/v1/balance?"+data)
        if not balances:
            raise Exception("Error when getting wallet balances")
        if "error" in balances:
            raise Exception(balances["error"]["message"])
        result = {}
        for address in addresses:
            result[address] = balances["addresses"][address]["confirmed"]["coins"]
        return result

    def _pickOutputsFromAddress(self, address, amount, minimum = 32):
        #Pick the output with less coin hours
        #but with at least 10 to be able to
        #return SKY to original address
        data = urllib.parse.urlencode({"addrs" : address})
        outputs = self.makeHttpRequest("api/v1/outputs?" + data)
        min_hours = 1000000000
        hashes = []
        minhash = ''
        total_hours = 0
        total_coins = 0
        for output in outputs["head_outputs"]:
            hours = output['hours']
            coins = float(output['coins'])
            if coins >= amount and hours >= minimum and hours < min_hours:
                min_hours = hours
                minhash = output['hash']
                total_hours = hours
                total_coins = coins
        if minhash != '':
            hashes = [minhash]
        else:
            #No output with enough coins and coin hours
            #Then find one with enough coin and another one
            #with enough coin hours
            total_hours = 0
            total_coins = 0
            outs = outputs["head_outputs"]
            outs.sort(key = lambda x: x["hours"])
            #find output with enough hours
            for output in outs:
                hours = output['hours']
                coins = float(output['coins'])
                if hours >= minimum:
                    hashes.append( output["hash"] )
                    total_hours += hours
                    total_coins += coins
                    break
            if len(hashes) > 0:
                #Now add more outputs to fulfill coins
                outs.sort(key = lambda x: x["coins"])
                for output in outs:
                    if output["hash"] == hashes[0]:
                        continue
                    hashes.append( output["hash"] )
                    hours = output['hours']
                    coins = float(output['coins'])
                    total_hours += hours
                    total_coins += coins
                    if total_coins >= amount:
                        break
        logging.debug("Picked outputs {} with {} hours and {} coins".\
            format(hashes, total_hours, total_coins))
        return hashes

    def _transferSKYEx(self, sourceAddress, destAddress, amount, outputs):
        tx = self.buildSingleTransaction(sourceAddress, destAddress, amount, outputs)
        self._sendTransaction(tx)

    def buildSingleTransaction(self, sourceAddress, destAddress, amount, outputs):
        amount = float(amount) / 1000000 #Convert to droplets
        logging.debug("******Transferring (Skycoin) from {} to {}, amount {}".format( \
            sourceAddress, destAddress, amount))
        sourceWallet = self.wallets[sourceAddress]["addressContext"]
        privateKey = self.wallets[sourceAddress]["privateKey"]
        tx = {
            "hours_selection": {
                "type": "auto",
                "mode": "share",
                "share_factor": "0.5"
            },
            "wallet": {
                "id": sourceWallet
            },
            "to" : [{
                "address" : destAddress,
                "coins" : "{:f}".format(amount)
            }]
        }
        if outputs:
            tx["wallet"]["unspents"] = outputs
        else:
            tx["wallet"]["addresses"] = [sourceAddress]
        return tx


    def _sendTransaction(self, tx):
        CSRF_token = self._getCSRFToken()
        logging.debug("Calling skycoin to create new transaction")
        response = app.lykke_session.post(form_url(app_config.SKYCOIN_NODE_URL,
                '/api/v1/wallet/transaction'),
                data=json.dumps(tx),
                headers={'X-CSRF-Token': CSRF_token['csrf_token'],
                "Content-Type" : "application/json"},
                verify = app_config.VERIFY_SSL)
        if response.status_code != 200:
            raise Exception("Error creating transaction: {}".format(response.text))
        transaction = response.json()
        if not transaction:
            logging.debug("Error creating transaction")
            raise Exception("Error creating transaction")
        if "error" in transaction:
            msg = "Error creating transaction: {} : {}".format(\
                transaction["error"]["code"],
                transaction["error"]["message"])
            raise Exception(msg)
        assert "encoded_transaction" in transaction, "Invalid transaction"
        encoded_transaction = transaction["encoded_transaction"]
        CSRF_token = self._getCSRFToken()
        data = {"rawtx" : encoded_transaction}
        broadcasted = False
        tries = 3
        while not broadcasted and tries > 0:
            tries -= 1
            logging.debug("Calling skycoin to broadcast transaction")
            response = app.lykke_session.post(form_url(app_config.SKYCOIN_NODE_URL,
                    '/api/v1/injectTransaction'),
                    data=json.dumps(data),
                    headers={'X-CSRF-Token': CSRF_token['csrf_token'],
                    "Content-Type" : "application/json"},
                    verify = app_config.VERIFY_SSL)
            if response.status_code != 200:
                if tries == 0:
                    raise Exception("Error broadcasting transaction: {}".format(response.text))
            else:
                broadcasted = True
        confirmed, hashHex = self._waitForTransactionConfirmation(encoded_transaction)
        if not confirmed:
            raise Exception("Transaction not confirmed")
        return hashHex

    def _waitForTransactionConfirmation(self, encoded_transaction):
        serialized = codecs.decode(encoded_transaction, 'hex')
        error, transaction_handle = skycoin.SKY_coin_TransactionDeserialize(serialized)
        self.assertEqual( error, 0, "Error deserializing signed transaction")
        self.assertNotEqual(transaction_handle, 0, "Invalid handle returned from SKY_coin_TransactionDeserialize")
        hash = skycoin.cipher_SHA256()
        error = skycoin.SKY_coin_Transaction_Hash(transaction_handle, hash)
        skycoin.SKY_handle_close(transaction_handle)
        self.assertEqual(error, 0, "Error getting transaction hash")
        #Get transaction hash to check for confirmation
        error, hashHex = skycoin.SKY_cipher_SHA256_Hex(hash)
        self.assertEqual(error, 0, "Error converting hash to hex")
        hashHex = str(hashHex)
        if hashHex.startswith("b\'"):
            hashHex = hashHex[2:len(hashHex)-1]
        timeOut = 5
        tries = 10
        confirmed = False
        innerHash = ''
        while tries > 0 and not confirmed:
            try:
                params={"txid": hashHex}
                json_response = self.makeHttpRequest("api/v1/transaction?" + urllib.parse.urlencode(params))
                if json_response:
                    if json_response['txn']['txid'].lower() != hashHex.lower():
                        raise Exception("Received transaction info for the wrong transaction." + \
                            " {} != {}".format(json_response['txn']['txid'], hashHex))
                    confirmed = json_response["status"]["confirmed"]
                    logging.debug("Confirmed result: {}".format(confirmed))
                    if confirmed:
                        logging.debug("Transaction confirmed: {}".format(json_response))
                        innerHash = json_response['txn']['inner_hash']
                        break
                else:
                    raise Exception("Invalid response from /api/v1/transaction. No response")
                if not confirmed:
                    logging.debug("Error getting transaction status or transaction not confirmed")
            except Exception as e:
                logging.debug("Error when checking transaction status. Error: {}".format(str(e)) )
            finally:
                tries -= 1
                if not confirmed:
                    time.sleep(timeOut)
        return confirmed, innerHash


    def _transferSKY(self, sourceAddress, destAddresses, amounts, operationId):
        logging.debug("******Transferring from {} to {}, amount {}, operation {}".format( \
            sourceAddress, str(destAddresses), str(amounts),
            operationId))
        assert len(destAddresses) > 0
        assert len(destAddresses) == len(amounts)
        sourceWallet = self.wallets[sourceAddress]["addressContext"]
        privateKey = self.wallets[sourceAddress]["privateKey"]

        transaction_context = ""

        if len(destAddresses) == 1:
            testTx = {
                'operationID' : operationId,
                'fromAddress' : sourceAddress,
                'fromAddressContext' : sourceWallet,
                'toAddress' : destAddresses[0],
                'assetId' : 'SKY',
                'amount' : str(amounts[0]), #1000 droplet
                'includeFee' : False
            }
            response = self.app.post(
                '/v1/api/transactions/single',
                data = json.dumps(testTx),
                content_type='application/json'
            )
            response_text = response.get_data(as_text=True)
            if response.status_code != 200:
                logging.debug("Error creating transaction: {}".format(response_text))
                return False, response.status_code, ""
            json_response = json.loads(response_text)
            self.assertIn('transactionContext', json_response)
            transaction_context = json_response['transactionContext']
        else:
            outputs = []
            i = 0
            for address in destAddresses:
                output = {
                    "toAddress" : address,
                    "amount" : str(amounts[i]) #1000 droplet
                }
                i += 1
                outputs.append(output)
            testTx = {
                'operationID' : operationId,
                'fromAddress' : sourceAddress,
                'fromAddressContext' : sourceWallet,
                'outputs' : outputs,
                'assetId' : 'SKY'
            }
            response = self.app.post(
                '/v1/api/transactions/many-outputs',
                data = json.dumps(testTx),
                content_type='application/json'
            )
            response_text = response.get_data(as_text=True)
            if response.status_code != 200:
                logging.debug("Error creating transaction: {}".format(response_text))
                return False, response.status_code, ""
            json_response = json.loads(response_text)
            self.assertIn('transactionContext', json_response)
            transaction_context = json_response['transactionContext']

        #Transaction sign
        data = {
            "privateKeys" : [privateKey],
            "transactionContext" : transaction_context
        }
        response = self.app.post(
            '/v1/api/sign',
            data = json.dumps(data),
            content_type='application/json'
        )
        response_text = response.get_data(as_text=True)
        if response.status_code != 200:
            logging.debug("Error signing transaction: {}".format(response_text))
            return False, response.status_code, ""
        json_response = json.loads(response_text)
        self.assertIn('signedTransaction', json_response)
        signedTransaction = json_response['signedTransaction']

        #Transaction broadcast
        data = {
            "operationId" : operationId,
            "signedTransaction" : signedTransaction,
        }
        tries = 3
        broadcasted = False
        while not broadcasted and tries > 0:
            tries -= 1
            response = self.app.post(
                '/v1/api/transactions/broadcast',
                data = json.dumps(data),
                content_type='application/json'
            )
            response_text = response.get_data(as_text=True)
            if response.status_code != 200:
                logging.debug("Error broadcasting transaction: {}".format(response_text))
                if tries == 0:
                    return False, response.status_code, ""
            else:
                broadcasted = True

        confirmed, hashHex = self._waitForTransactionConfirmation(signedTransaction)
        if not confirmed:
            raise Exception("Error, transaction not confirmed")
        return True, 200, hashHex

    def _pickAddress(self, minAmount, minCoinHours):
        mainWallet = self.wallets[self.mainAddress]
        walletName = mainWallet["addressContext"]
        balance = self.makeHttpRequest("api/v1/wallet/balance?id=" + \
                walletName)
        logging.debug("Wallet balance: {}".format(balance))
        pickedAddress = ''
        pickedCoins = 0
        pickedHours = 0
        addresses = []
        for address in balance["addresses"].keys():
            if address == self.mainAddress:
                continue
            a = {
                "coins" : balance["addresses"][address]["confirmed"]["coins"],
                "hours" : balance["addresses"][address]["confirmed"]["hours"],
                "address" : address
            }
            addresses.append(a)
        addresses.sort(key = lambda x : x["hours"])
        #Pick an address with balance and coin hours
        for address in addresses:
            coins = address["coins"]
            hours = address["hours"]
            if coins >= minAmount and hours >= minCoinHours:
                address = address["address"]
                result = self.makeHttpRequest("lock?n={}".format(address),
                    None, None, SYNCHRONIZATION_SERVER)
                if "index" in result:
                    pickedAddress = address
                    logging.debug("Found address: {}".format(pickedAddress))
                    pickedCoins = coins
                    pickedHours = hours
                    break
        logging.debug("Picked address:{}".format(pickedAddress))
        return pickedAddress

    #Just any address to test a transactions
    #that should fail. The address doesnt require
    #balance
    def _pickAnyAddress(self):
        return "iZfykDvX1YD2NJJ5UTLfZFfXQBSkpCg9FW"

    def _lockAddress(self):
        mainWallet = self.wallets[self.mainAddress]
        walletName = mainWallet["addressContext"]
        balance = self.makeHttpRequest("api/v1/wallet/balance?id=" + \
                walletName)
        for address in balance["addresses"].keys():
            if address == self.mainAddress:
                continue
            result = self.makeHttpRequest("lock?n={}".format(address),
                None, None, SYNCHRONIZATION_SERVER)
            if "index" in result:
                logging.debug("Locked address: {}".format(address))
                self.lockedAddresses[address] = True
                return address
        return Exception("Unable to lock an address for testing")

    def _freeAddress(self, address):
        self.lockedAddresses[address] = False
        self.makeHttpRequest("free?n={}".format(address),
            None, None, SYNCHRONIZATION_SERVER)

    def _lockMainAddress(self):
        locked = False
        tries = 100
        while not locked and tries > 0:
            result = self.makeHttpRequest("lock?n={}".format(self.mainAddress),
                None, None, SYNCHRONIZATION_SERVER)
            if "index" in result:
                self.lockedAddresses[self.mainAddress] = True
                locked = True
            else:
                time.sleep(1)
                tries -= 1

    def _freeMainAddress(self):
        self.lockedAddresses[self.mainAddress] = False
        self.makeHttpRequest("free?n={}".format(self.mainAddress),
            None, None, SYNCHRONIZATION_SERVER)

    def _getSomeSkyForTest(self, toAddress, amount, minCoinHours):
        logging.debug("Reserving {},{} for {}".format(amount, minCoinHours,
                toAddress))
        #Pick an output with enough coin hours that will allow
        #subsequent transfers
        self._lockMainAddress()
        outputs = self._pickOutputsFromAddress(self.mainAddress, amount / 1e6,
            minCoinHours)
        if len(outputs) == 0:
            self._freeMainAddress()
            return False
        balance = self._getBalanceForAddresses([self.mainAddress,
            toAddress])
        logging.debug("Balance: {}".format(balance))
        self._transferSKYEx(self.mainAddress,
            toAddress, amount, outputs)
        balance = self._getBalanceForAddresses([self.mainAddress,
            toAddress])
        self._freeMainAddress()
        logging.debug("Balance: {}".format(balance))
        return True

    def _getSpendableOutputsForAddresses(self, addresses):
        data = {"addrs": ",".join(addresses)}
        data = urllib.parse.urlencode(data)
        spendables = []
        outputs = self.makeHttpRequest("api/v1/outputs?"+data)
        total = 0
        for output in outputs["head_outputs"]:
            coins = float(output["coins"])
            hours = output["hours"]
            if coins >= 0.0009 and hours >= 1:
                spendables.append( output )
                total += coins
        return spendables, total

    def _recoverOutputs(self, addresses, dest):
        for address in addresses:
            outputs, total = self._getSpendableOutputsForAddresses([address])
            logging.debug("Outputs to recover: {}. Total: {}".format(outputs, total))
            self._transferSKYEx(address, dest, total, outputs)

    def _pickAddresses(self):
        sourceAddress1 = ''
        sourceAddress2 = ''
        #Find an address with 3000 droplets and at least 4 coin hours
        address = self._pickAddress(3000, 4)
        logging.debug("Found address '{}' with at leat 3000 coins and 4 hours".\
            format(address))
        if address == '':
            sourceAddress2 = self._pickAddress(2000, 1)
            sourceAddress1 = self._pickAddress(1000, 1)
        else:
            sourceAddress1 = address
            sourceAddress2 = address
        reserved = False
        if sourceAddress1 == ''  and sourceAddress2 == '':
            sourceAddress1 = self._lockAddress()
            sourceAddress2 = sourceAddress1
            reserved = self._getSomeSkyForTest(sourceAddress1, 3000, 16)
            if not reserved:
                sourceAddress2 = ''
                reserved = self._getSomeSkyForTest(sourceAddress1, 1000, 4)
        if sourceAddress1 == '':
            sourceAddress1 = self._lockAddress()
            self._getSomeSkyForTest(sourceAddress1, 1000, 4)
        if sourceAddress2 == '':
            sourceAddress2 = self._lockAddress()
            self._getSomeSkyForTest(sourceAddress2, 2000, 4)
        logging.debug("address1 : {}, address2: {}".format(sourceAddress1,
                sourceAddress2))
        return sourceAddress1, sourceAddress2

    def _findInHistory(self, history, source, dest, amount, hash):
        found = False
        for tx in history:
            if tx['hash'] == hash:
                if tx['fromAddress'] != source:
                    continue
                if tx['toAddress'] != dest:
                    continue
                txAmount = float(tx['amount'])
                if abs(txAmount - amount) >= 0.00001:
                    continue
                self.assertEqual(tx['assetId'], 'SKY',
                    "{} != SKY".format(tx['assetId']))
                found = True
                break
        self.assertTrue(found)

    def _hexToB64(self, s):
        r = base64.b64encode(bytes.fromhex(s))
        r = str(r)
        if r.startswith("b\'"):
            r = r[2:len(r)-1]
        return r

    def _checkTransactionSingleHistory(self, source, dest, amount, hash):
        logging.debug("Tx to search in history in hex: {}".format(hash))
        hash = self._hexToB64(hash)
        logging.debug("Checking single transaction history. " + \
            "hash: {}, source: {}, dest: {} ".format(hash, source, dest))
        coins = amount / 1e6
        historyFrom = self._getHistoryFrom(source)
        historyTo = self._getHistoryTo(dest)
        self._findInHistory(historyFrom, source, dest, coins, hash)
        self._findInHistory(historyTo, source, dest, coins, hash)


    def _checkTransactionSingle(self, source, dest):
        previousBalance = self._getBalanceForAddresses([source,
                            dest])
        logging.debug("Balance: {}".format(previousBalance))
        ok, status, hashHex = self._transferSKY(source, [dest], [1000],
                '4324432444332') #just some operation id
        self.assertTrue(ok)
        self.assertEqual(status, 200)
        self._checkTransactionSingleHistory(source, dest, 1000, hashHex)
        newBalance = self._getBalanceForAddresses([source,
                dest])
        logging.debug("Balance: {}".format(newBalance))
        self._checkBalances([{'address' : source,
            'balance' : newBalance[source]},
            {'address' : dest,
                'balance' : newBalance[dest]}])
        self.assertEqual(previousBalance[source],
            newBalance[source] + 1000,
            "Address {0} should have lost 1000 droplets".format(source))
        self.assertEqual(previousBalance[dest],
            newBalance[dest] - 1000,
            "Address {0} should have gained 1000 droplets".format(dest))
        #Test creating a broadcasted transaction
        ok, status, hashHex = self._transferSKY(source, [dest], [1000],
                '4324432444332') #just some operation id
        self.assertFalse(ok) #Already broadcasted
        self.assertEqual(status, 409)

    def _checkTransactionManyOutputsHistory(self, source, dest1, dest2, amount, hash):
        logging.debug("Tx to search in history in hex: {}".format(hash))
        hash = self._hexToB64(hash)
        logging.debug("Checking many outputs transaction history. " + \
            "hash: {}, source: {}, dest: {}, dest2: {} "\
                .format(hash, source, dest1, dest2))
        coins = amount / 1e6
        historyFrom = self._getHistoryFrom(source)
        historyTo1 = self._getHistoryTo(dest1)
        historyTo2 = self._getHistoryTo(dest2)
        logging.debug("history from: {}".format(historyFrom))
        logging.debug("history to1: {}".format(historyTo1))
        logging.debug("history to2: {}".format(historyTo2))
        self._findInHistory(historyFrom, source, dest1, coins, hash)
        self._findInHistory(historyFrom, source, dest2, coins, hash)
        self._findInHistory(historyTo1, source, dest1, coins, hash)
        self._findInHistory(historyTo2, source, dest2, coins, hash)

    def _checkTransactionManyOutputs(self, source, dest1, dest2):
        previousBalance = self._getBalanceForAddresses([source,
                            dest1, dest2])
        logging.debug("Balance: {}".format(previousBalance))
        ok, status, hashHex = self._transferSKY(source, [dest1, dest2], [1000, 1000],
                '8986575765') #just some operation id
        self.assertEqual(status, 200)
        self.assertTrue(ok)
        self._checkTransactionManyOutputsHistory(source, dest1, dest2, 1000, hashHex)
        newBalance = self._getBalanceForAddresses([source,
                            dest1, dest2])
        logging.debug("Balance: {}".format(newBalance))
        self._checkBalances([{'address' : source,
            'balance' : newBalance[source]},
            {'address' : dest1,
                'balance' : newBalance[dest1]},
            {'address' : dest2,
                'balance' : newBalance[dest2]}])
        self.assertEqual(previousBalance[source],
            newBalance[source] + 2000,
            "Address {0} should have lost 2000 droplets".format(source))
        self.assertEqual(previousBalance[dest1],
            newBalance[dest1] - 1000,
            "Address {0} should have gained 1000 droplets".format(dest1))
        self.assertEqual(previousBalance[dest2],
            newBalance[dest2] - 1000,
            "Address {0} should have gained 1000 droplets".format(dest2))
        #Test creating a broadcasted transaction
        ok, status, hashHex = self._transferSKY(source, [dest1, dest2], [1000, 1000],
                '8986575765') #just some operation id
        self.assertFalse(ok) #Already broadcasted
        self.assertEqual(status, 409)

    def _addToHistoryObservations(self, fromAddresses, toAddresses):
        for address in fromAddresses:
            response = self.app.post(
                "/v1/api/transactions/history/from/{}/observation".format(address)
            )
            self.assertEqual(response.status_code, 200)
        for address in toAddresses:
            response = self.app.post(
                "/v1/api/transactions/history/to/{}/observation".format(address)
            )
            self.assertEqual(response.status_code, 200)

    def _removeFromHistoryObservations(self, fromAddresses, toAddresses):
        for address in fromAddresses:
            response = self.app.delete(
                "/v1/api/transactions/history/from/{}/observation".format(address)
            )
            self.assertEqual(response.status_code, 200)
        for address in toAddresses:
            response = self.app.delete(
                "/v1/api/transactions/history/to/{}/observation".format(address)
            )
            self.assertEqual(response.status_code, 200)

    def _checkBalances(self, addressBalances):
        response = self.app.get("/v1/api/balances?take=500")
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        logging.debug("Balances: {}".format(json_response))
        for address in addressBalances:
            if address['balance'] == 0: #no zero balances
                continue
            addressFound = False
            for item in json_response['items']:
                if address['address'] == item['address']:
                    item_balance = float(item['balance'])
                    item_balance = round(item_balance, 6)
                    item_balance *= 1e6
                    if address['balance'] == item_balance:
                        addressFound = True
                        break
            self.assertTrue(addressFound,
                "Address: {} not match in balance result".format(address))


    def _addToBalanceObservations(self, addresses):
        for address in addresses:
            response = self.app.post(
                "/v1/api/balances/{}/observation".format(address)
            )
            self.assertEqual(response.status_code, 200)

    def _removeFromBalanceObservations(self, addresses):
        for address in addresses:
            response = self.app.delete(
                "/v1/api/balances/{}/observation".format(address)
            )
            self.assertEqual(response.status_code, 200)

    def _checkNotObservedHistoryFail(self, source, dest):
        response = self.app.get(
            "/v1/api/transactions/history/from/{}?take=500".format(source)
        )
        self.assertEqual(response.status_code, 204)
        response = self.app.get(
            "/v1/api/transactions/history/to/{}?take=500".format(dest)
        )
        self.assertEqual(response.status_code, 204)

    def _getHistoryFrom(self, address):
        response = self.app.get(
            "/v1/api/transactions/history/from/{}?take=500".format(address)
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        return json_response

    def _getHistoryTo(self, address):
        response = self.app.get(
            "/v1/api/transactions/history/to/{}?take=500".format(address)
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        return json_response

    def _getTestWallets(self):
        seeds_path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                *('data/skycoin/seeds.json'.split('/')))
        file = open(seeds_path, "r")
        text = file.read()
        r = json.loads(text)
        file.close()
        wallets = {}
        for seed in r["seeds"]:
            pubkey = skycoin.cipher_PubKey()
            seckey = skycoin.cipher_SecKey()
            error = skycoin.SKY_cipher_GenerateDeterministicKeyPair(
                    seed.encode(), pubkey, seckey)
            if error != 0:
                raise Exception("Error when creating private and public keys for wallet")

            wallet = {
                "seed" : seed,
                "privateKey": binascii.hexlify(bytearray(seckey.toStr())).decode('ascii'),
                "publicKey": binascii.hexlify(bytearray(pubkey.toStr())).decode('ascii')
            }
            wallets[wallet["publicKey"]] = wallet
        wallets = self._matchServerWallets(wallets)
        wallets = self._createMissingWallets(wallets)
        return wallets

    def _createMissingWallets(self, wallets):
        i = 0
        newWallets = {}
        for key in wallets.keys():
            wallet = wallets[key]
            if not "addressContext" in wallet:
                i += 1
                newWallet = self._createWalletFromSeed(wallet["seed"],
                    "testwallet" + str(i))
                wallet["addressContext"] = newWallet["addressContext"]
                wallet["publicAddress"] = newWallet["publicAddress"]
                assert wallet["privateKey"] == newWallet["privateKey"], "{} != {}".format(wallet["privateKey"], newWallet["privateKey"])
                assert wallet["publicKey"] == newWallet["publicKey"], "{} != {}".format(wallet["publicKey"], newWallet["publicKey"])
                #new created wallet should have 1 address
                wallet["entries_count"] = 1
            newWallets[wallet["publicAddress"]] = wallet
        return newWallets

    def _matchServerWallets(self, wallets):
        serverWallets = self.makeHttpRequest( "api/v1/wallets" )
        if serverWallets is None:
            raise Exception("No response when getting wallets")
        matched = 0
        for wallet in serverWallets:
            walletName = wallet["meta"]["filename"]
            for entry in wallet["entries"]:
                pubkey = entry["public_key"]
                if pubkey in wallets:
                    wallets[pubkey]["addressContext"] = walletName
                    wallets[pubkey]["publicAddress"] = entry["address"]
                    wallets[pubkey]["entries_count"] = len(wallet["entries"])
                    matched += 1
                    break
            if matched == len(wallets):
                break
        return wallets

    def _getCSRFToken(self):
        # generate CSRF token
        tries = 1
        if not LiveTestCase.serverUp:
            tries = 50
        timeOut = 5
        CSRF_token = False
        i = 1
        while tries > 0:
            print("Connecting to skycoin node. Try: {}".format(i))
            logging.debug("Connecting to skycoin node. Try: {}".format(i))
            i += 1
            try:
                CSRF_token = self.makeHttpRequest("api/v1/csrf")
                if CSRF_token and "csrf_token" in CSRF_token:
                    break
            except Exception as e:
                logging.debug("Error requesting csrf token. Error: {}".format(e))
                time.sleep(timeOut)
            tries -= 1
        if not CSRF_token or "csrf_token" not in CSRF_token:
            assert False, "Error requesting token"
        LiveTestCase.serverUp = True
        return CSRF_token

    def _createWalletFromSeed(self, seed, label):
        CSRF_token = self._getCSRFToken()
        logging.debug("Calling skycoin to create wallet with seed")
        # create the wallet from seed
        data = {"seed": seed, "label": label, "scan": "5"}
        headers = {'X-CSRF-Token': CSRF_token['csrf_token']}
        new_wallet = self.makeHttpRequest("api/v1/wallet/create", data, headers)

        if not new_wallet:
            raise Exception("No response when creating wallet")

        if not new_wallet or "entries" not in new_wallet:
            raise Exception("Error when creating wallet")

        pubkey = skycoin.cipher_PubKey()
        seckey = skycoin.cipher_SecKey()
        error = skycoin.SKY_cipher_GenerateDeterministicKeyPair(
                seed.encode(), pubkey, seckey)
        if error != 0:
            raise Exception("No response when creating private and public keys for wallet")

        result = {
            "privateKey": binascii.hexlify(bytearray(seckey.toStr())).decode('ascii'),
            "publicKey": binascii.hexlify(bytearray(pubkey.toStr())).decode('ascii'),
            "publicAddress": new_wallet["entries"][0]["address"],
            "addressContext": new_wallet['meta']['filename']
        }
        logging.debug("Wallet created {}".format(str(result["publicAddress"])))
        return result

    def _recreateWalletAddresses(self):
        addresses = []
        mainWallet = self.wallets[self.mainAddress]
        wallet_entries = mainWallet["entries_count"]
        logging.debug("Wallet with main address {} has {} addresses".format( \
            self.mainAddress, wallet_entries))
        seed = mainWallet["seed"]
        seed = seed.encode()
        pubkey = skycoin.cipher_PubKey()
        seckey = skycoin.cipher_SecKey()
        i = 0
        while i < wallet_entries:
            error, new_seed = \
                skycoin.SKY_cipher_DeterministicKeyPairIterator(seed,
                pubkey, seckey)
            self.assertEqual(error, 0, "Error with SKY_cipher_DeterministicKeyPairIterator")
            address = skycoin.cipher__Address()
            err = skycoin.SKY_cipher_AddressFromPubKey(pubkey, address)
            self.assertEqual(error, 0, "Error creating address from pub key.")
            error, strAddress = skycoin.SKY_cipher_Address_String(address)
            self.assertEqual(error, 0, "Error with SKY_cipher_Address_String")
            strAddress = str(strAddress)
            if strAddress.startswith("b\'"):
                strAddress = strAddress[2:len(strAddress)-1]
            i += 1
            seed = new_seed
            if strAddress == self.mainAddress:
                continue
            logging.debug("Address generated: {}".format(strAddress))
            newWallet = {
                "privateKey": binascii.hexlify(bytearray(seckey.toStr())).decode('ascii'),
                "publicKey": binascii.hexlify(bytearray(pubkey.toStr())).decode('ascii'),
                "publicAddress": strAddress,
                "addressContext": mainWallet["addressContext"]
            }
            self.wallets[strAddress] = newWallet

    def _unlockIndexes(self, indexes):
        logging.debug("Unlocking indexes: {}".format(indexes))
        data = {"n": ",".join(str(x) for x in indexes)}
        url = "free?" + urllib.parse.urlencode(data)
        result = self.makeHttpRequest(url, None, None, SYNCHRONIZATION_SERVER)

    def makeHttpRequest(self, url, data = None, headers = None, server = False):
        if not server:
            server = app_config.SKYCOIN_NODE_URL
        if data:
            data = urllib.parse.urlencode(data)
            data = data.encode()
        logging.debug("Making request to {}".format(url.split("?")[0]))
        request = urllib.request.Request(server + url)
        if headers:
            for key in headers.keys():
                request.add_header(key, headers[key])
        response = urllib.request.urlopen(request, data)
        if not response:
            logging.debug("Error. No response from {}".format(url))
            raise Exception("Error. No response from {}".format(url))
        result = str(response.read().replace(b'\n', b''))
        if result.startswith("b\'"):
            result = result[2:len(result)-1]
        return json.loads(result)

def form_url(base, path):
    """
    Conform the full URL from base URL and path
    """

    if path[0] != '/':
        path = '/' + path

    if base[len(base) - 1] == '/':
        base = base[0:len(base) - 1]

    url = base + path

    return url


def get_url(path, values=""):
    """
    General GET function for blockchain
    """

    url = form_url(app_config.SKYCOIN_NODE_URL, path)

    # resp = requests.get(url, params = values)
    # response_data = resp.json()

    response_data = {"Called": "get_url()", "url": url, "values:": values}

    return response_data


def post_url(path, values=""):
    """
    General POST function for blockchain
    """

    url = form_url(app_config.SKYCOIN_NODE_URL, path)

    # resp = requests.post(url, data = values)
    # response_data = resp.json()

    response_data = {"Called": "post_url()", "url": url, "values:": values}

    return response_data
