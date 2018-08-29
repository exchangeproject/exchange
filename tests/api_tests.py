import binascii
import json
import unittest

import skycoin

from exchange_app import app
from exchange_app.settings import app_config

# Removed endpoints
URL_PENDING_EVENTS_CASHIN            = '/v1/api/pending-events/cashin'
URL_PENDING_EVENTS_CASHOUT_START     = '/v1/api/pending-events/cashout-started'
URL_PENDING_EVENTS_CASHOUT_COMPLETED = '/v1/api/pending-events/cashout-completed'
URL_PENDING_EVENTS_CASHOUT_FAILED    = '/v1/api/pending-events/cashout-failed'
URL_WALLET_CASHOUT                   = '/v1/api/wallets/{address}/cashout'
# Current API
URL_ADDRESS_VALIDITY = '/v1/api/addresses/{address}/validity'
URL_BALANCE_ADDRESS  = '/v1/api/balances/{address}/observation'
URL_ASSETS           = '/v1/api/assets'
URL_ASSET            = '/v1/api/assets/{id}'
URL_WALLET_NEW       = '/v1/api/wallets'
URL_ISALIVE          = '/v1/api/isalive'
URL_CAPABILITIES     = '/v1/api/capabilities'
URL_SIGN             = '/v1/api/sign'
URL_CONSTANTS        = '/v1/api/constants'
URL_ADDRESS_EXPLORER = '/v1/api/addresses/{address}/explorer-url'
URL_ADDRESS_OBSERVE  = '/v1/api/balances/{address}/observation'
URL_BALANCES_FIRST   = '/v1/api/balances?take={limit}'
URL_BALANCES_PAGE    = '/v1/api/balances?take={limit}&continuation={offset}'
URL_BALANCES_PAGE    = '/v1/api/isalive'

ADDRESS_VALID = r'2GgFvqoyk9RjwVzj8tqfcXVXB4orBwoc9qv'
ADDRESS_INVALID = r'12345678'
ADDRESSES_WITH_COINS = [r'2THDupTBEo7UqB6dsVizkYUvkKq82Qn4gjf', r'qxmeHkwgAMfwXyaQrwv9jq3qt228xMuoT5']


class BaseApiTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()


class ApiTestCase(BaseApiTestCase):
    def test_isalive(self):
        response = self.app.get(URL_ISALIVE)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIn("name", json_response)
        self.assertIn("version", json_response)
        self.assertIn("env", json_response)
        self.assertIn("isDebug", json_response)
        self.assertIn("contractVersion", json_response)
        self.assertEqual(json_response["name"], app_config.SKYCOIN_FIBER_NAME)
        self.assertEqual(json_response["version"], '0.24.1')
        self.assertEqual(json_response["env"], 'Dev')
        self.assertEqual(json_response["isDebug"], True)
        self.assertEqual(json_response["contractVersion"], app_config.LYKKE_API_VERSION)

    def test_address_valid(self):
        address = ADDRESS_VALID
        response = self.app.get(URL_ADDRESS_VALIDITY.format(address=address))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['isValid'], True)

    def test_address_invalid(self):
        address = ADDRESS_INVALID
        response = self.app.get(URL_ADDRESS_VALIDITY.format(address=address))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['isValid'], False)

    def test_get_assets(self):
        response = self.app.get(URL_ASSETS, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIn('continuation', json_response)
        self.assertIn('items', json_response)

        asset_record = json_response['items'][0]
        self.assertEqual(asset_record['assetId'],  'SKY')
        self.assertEqual(asset_record['address'],  '')
        self.assertEqual(asset_record['name'],     'Skycoin')
        self.assertEqual(asset_record['accuracy'], '6')

    def test_get_asset(self):
        response = self.app.get(URL_ASSET.format(id='SKY'), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))

        asset_record = json_response
        self.assertEqual(asset_record['assetId'],  'SKY')
        self.assertEqual(asset_record['address'],  '')
        self.assertEqual(asset_record['name'],     'Skycoin')
        self.assertEqual(asset_record['accuracy'], '6')

    def test_get_asset_wrong_id(self):
        response = self.app.get(URL_ASSET.format(id='UNKCOIN'), content_type='application/json')
        self.assertEqual(response.status_code, 204)

    def test_wallets(self):
        response = self.app.post(URL_WALLET_NEW, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIn('privateKey', json_response)
        self.assertIn('publicAddress', json_response)
        seckey = skycoin.cipher_SecKey()
        err = skycoin.SKY_cipher_NewSecKey(binascii.unhexlify(json_response['privateKey']), seckey)
        self.assertEqual(err, 0)
        address = skycoin.cipher__Address()
        err = skycoin.SKY_cipher_AddressFromSecKey(seckey, address)
        self.assertEqual(err, 0)
        err, addressStr = skycoin.SKY_cipher_Address_String(address)
        self.assertEqual(err, 0)
        self.assertEqual(addressStr.decode('ascii'), json_response['publicAddress'])

    def test_is_alive(self):
        response = self.app.get(URL_ISALIVE, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIn('name', json_response)
        self.assertIn('version', json_response)
        self.assertIn('env', json_response)
        self.assertIn('isDebug', json_response)

    def test_api_capabilities(self):
        response = self.app.get(URL_CAPABILITIES, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIn('isTransactionsRebuildingSupported', json_response)
        self.assertIn('areManyInputsSupported', json_response)
        self.assertIn('areManyOutputsSupported', json_response)
        self.assertIn("isTestingTransfersSupported", json_response)
        self.assertIn("isPublicAddressExtensionRequired", json_response)
        self.assertIn("isReceiveTransactionRequired", json_response)
        self.assertIn("canReturnExplorerUrl", json_response)
        self.assertEqual(json_response['isTransactionsRebuildingSupported'], False)
        self.assertEqual(json_response['areManyInputsSupported'], not app_config.SKYCOIN_WALLET_SHARED)
        self.assertEqual(json_response['areManyOutputsSupported'], True)
        self.assertEqual(json_response['isTestingTransfersSupported'], False)
        self.assertEqual(json_response['isPublicAddressExtensionRequired'], False)
        self.assertEqual(json_response['isReceiveTransactionRequired'], False)
        self.assertEqual(json_response['canReturnExplorerUrl'], True)

    def test_sign_noparams(self):
        response = self.app.post(URL_SIGN, content_type='application/json')
        #test response code is 400 without parameters
        self.assertEqual(response.status_code, 400)

    def test_constants(self):
        response = self.app.get(URL_CONSTANTS, content_type='application/json')
        #test constants not implemented
        self.assertEqual(response.status_code, 501)

    def test_explorer_url(self):
        response = self.app.get(URL_ADDRESS_EXPLORER.format(address=ADDRESS_VALID), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertListEqual(json_response,
                ['https://explorer.skycoin.net/app/address/2GgFvqoyk9RjwVzj8tqfcXVXB4orBwoc9qv'])

    def test_explorer_url_noaddr(self):
        response = self.app.get(URL_ADDRESS_EXPLORER.format(address=''), content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_explorer_url_invalid(self):
        response = self.app.get(URL_ADDRESS_EXPLORER.format(address=ADDRESS_INVALID), content_type='application/json')
        self.assertEqual(response.status_code, 204)

    def test_observe_invalid_address(self):
        response = self.app.post(URL_ADDRESS_OBSERVE.format(address=ADDRESS_INVALID),
                content_type='application/json')
        self.assertEqual(response.status_code, 422)

        # Repeat and get the same
        response = self.app.post(URL_ADDRESS_OBSERVE.format(address=ADDRESS_INVALID),
                content_type='application/json')
        self.assertEqual(response.status_code, 422)

    def test_observe_address_nocoins(self):
        # Address not in observation list
        response = self.app.get(URL_BALANCES_FIRST.format(limit=100),
                content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIn('items', json_response)
        resultset = [item for item in json_response['items']
                if 'address' in item and item['address'] == ADDRESS_VALID]
        self.assertListEqual([], resultset)
        # Observe address
        response = self.app.post(URL_ADDRESS_OBSERVE.format(address=ADDRESS_VALID),
                content_type='application/json')
        self.assertEqual(response.status_code, 200)
        # Repeat and get conflict
        response = self.app.post(URL_ADDRESS_OBSERVE.format(address=ADDRESS_VALID),
                content_type='application/json')
        self.assertEqual(response.status_code, 409)
        # Address not in observation list. No balance
        response = self.app.get(URL_BALANCES_FIRST.format(limit=100),
                content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIn('items', json_response)
        resultset = [item for item in json_response['items']
                if 'address' in item and item['address'] == ADDRESS_VALID]
        self.assertEqual(0, len(resultset))

    def test_observe_address(self):
            address1, address2 = ADDRESSES_WITH_COINS
            # Addresses not in observation list
            response = self.app.get(URL_BALANCES_FIRST.format(limit=100),
                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.get_data(as_text=True))
            self.assertIn('items', json_response)
            resultset = [item for item in json_response['items']
                    if 'address' in item and item['address'] in ADDRESSES_WITH_COINS]
            self.assertListEqual([], resultset)

            # Observe first address
            response = self.app.post(URL_ADDRESS_OBSERVE.format(address=address1),
                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
            # First address in observation list.
            response = self.app.get(URL_BALANCES_FIRST.format(limit=100),
                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.get_data(as_text=True))
            self.assertIn('items', json_response)
            self.assertTrue(len(json_response['items']) > 0)
            resultset = [item for item in json_response['items']
                    if 'address' in item and item['address'] in ADDRESSES_WITH_COINS]
            self.assertEqual(1, len(resultset))
            item = resultset[0]
            self.assertIn('address', item)
            self.assertIn('assetId', item)
            self.assertIn('balance', item)
            self.assertIn('block', item)
            self.assertEqual(item['address'], address1)
            self.assertEqual(item['assetId'], app_config.SKYCOIN_FIBER_ASSET)
            self.assertEqual(item['balance'], '1000000.0')

            # Observe second address
            response = self.app.post(URL_ADDRESS_OBSERVE.format(address=address2),
                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
            # Second address in observation list.
            response = self.app.get(URL_BALANCES_FIRST.format(limit=100),
                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.get_data(as_text=True))
            self.assertIn('items', json_response)
            resultset = [item for item in json_response['items']
                    if 'address' in item and item['address'] in ADDRESSES_WITH_COINS]
            self.assertEqual(2, len(resultset))
            # Assertions for 1st item
            item = resultset[0]
            self.assertIn('address', item)
            self.assertIn('assetId', item)
            self.assertIn('balance', item)
            self.assertIn('block', item)
            self.assertIn(item['address'], ADDRESSES_WITH_COINS)
            self.assertEqual(item['assetId'], app_config.SKYCOIN_FIBER_ASSET)
            self.assertEqual(item['block'], 180)
            # Assertions for first item
            item = resultset[1]
            self.assertIn('address', item)
            self.assertIn('assetId', item)
            self.assertIn('balance', item)
            self.assertIn('block', item)
            self.assertIn(item['address'], ADDRESSES_WITH_COINS)
            self.assertEqual(item['assetId'], app_config.SKYCOIN_FIBER_ASSET)
            self.assertEqual(item['block'], 180)
            # Ensure there are records for both addresses
            self.assertNotEqual(resultset[0]['address'], resultset[1]['address'])
            # Assertions on balances
            balances = {item['address'] : item['balance'] for item in resultset}
            self.assertDictEqual(balances, {address1: '1000000.0', address2: '22100.0'})

            # Repeat observation and get conflict
            response = self.app.post(URL_ADDRESS_OBSERVE.format(address=address1),
                    content_type='application/json')
            self.assertEqual(response.status_code, 409)

            # Delete observations
            response = self.app.delete(URL_ADDRESS_OBSERVE.format(address=ADDRESS_INVALID),
                    content_type='application/json')
            self.assertEqual(response.status_code, 204)
            response = self.app.get(URL_BALANCES_FIRST.format(limit=100),
                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.get_data(as_text=True))
            self.assertIn('items', json_response)
            resultset = set(item['address'] for item in json_response['items']
                    if 'address' in item and item['address'] in ADDRESSES_WITH_COINS)
            self.assertSetEqual(resultset, set(ADDRESSES_WITH_COINS))

            response = self.app.delete(URL_ADDRESS_OBSERVE.format(address=address1),
                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
            response = self.app.get(URL_BALANCES_FIRST.format(limit=100),
                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.get_data(as_text=True))
            self.assertIn('items', json_response)
            resultset = set(item['address'] for item in json_response['items']
                    if 'address' in item and item['address'] in ADDRESSES_WITH_COINS)
            self.assertSetEqual(resultset, set([address2]))

            response = self.app.delete(URL_ADDRESS_OBSERVE.format(address=address1),
                    content_type='application/json')
            self.assertEqual(response.status_code, 204)
            response = self.app.get(URL_BALANCES_FIRST.format(limit=100),
                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
            json_response = json.loads(response.get_data(as_text=True))
            self.assertIn('items', json_response)
            resultset = set(item['address'] for item in json_response['items']
                    if 'address' in item and item['address'] in ADDRESSES_WITH_COINS)
            self.assertSetEqual(resultset, set([address2]))


class DeprecatedApiTests(BaseApiTestCase):

    def assert_get_not_found(self, template, **args):
        url = template.format(**args)
        response = self.app.get(url, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_pending_events_cashin(self):
        self.assert_get_not_found(URL_PENDING_EVENTS_CASHIN)

    def test_pending_events_cashout_started(self):
        self.assert_get_not_found(URL_PENDING_EVENTS_CASHOUT_START)

    def test_pending_events_cashout_completed(self):
        self.assert_get_not_found(URL_PENDING_EVENTS_CASHOUT_COMPLETED)

    def test_pending_events_cashout_failed(self):
        self.assert_get_not_found(URL_PENDING_EVENTS_CASHOUT_FAILED)

    def test_wallets_cashout(self):
        self.assert_get_not_found(URL_WALLET_CASHOUT,address=r'2GgFvqoyk9RjwVzj8tqfcXVXB4orBwoc9qv')


if __name__ == '__main__':
    unittest.main()
