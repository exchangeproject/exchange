import json
import unittest
from exchange_app import app


class APITestCase(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def test_address_valid(self):
        data = dict(address=r'2GgFvqoyk9RjwVzj8tqfcXVXB4orBwoc9qv')
        response = self.app.get(
            '/api/v1.0/addresses/{}/isvalid'.format(data),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['isValid'], True)

    def test_address_invalid(self):
        data = dict(address=r'12345678')
        response = self.app.get(
            '/api/v1.0/addresses/{}/isvalid'.format(data),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['isValid'], False)

    def test_get_assets(self):
        response = self.app.get(
            '/api/v1.0/assets', content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_get_asset(self):
        data = dict(assetid=1)
        response = self.app.get(
            '/api/v1.0/assets',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_pending_events_cashin(self):
        response = self.app.get(
            '/api/v1.0/pending-events/cashin',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_pending_events_cashout_started(self):
        response = self.app.get(
            '/api/v1.0/pending-events/cashout-started',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_pending_events_cashout_completed(self):
        response = self.app.get(
            '/api/v1.0/pending-events/cashout-completed',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_pending_events_cashout_failed(self):
        response = self.app.get(
            '/api/v1.0/pending-events/cashout-failed',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_wallets(self):
        response = self.app.post(
            '/api/v1.0/wallets',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIn('privateKey', json_response)
        self.assertIn('address', json_response)

    def test_wallets_cashout(self):
        # FIXME Gives 400?
        data = dict(address=r'2GgFvqoyk9RjwVzj8tqfcXVXB4orBwoc9qv')
        response = self.app.post(
            '/api/v1.0/wallets/{}/cashout'.format(data),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_is_alive(self):
        response = self.app.get(
            '/api/v1.0/isalive', content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIn('name', json_response)
        self.assertIn('version', json_response)
        self.assertIn('env', json_response)
        self.assertIn('isDebug', json_response)

    def test_api_capabilities(self):
        response = self.app.get(
            '/api/v1.0/capabilities', content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIn('isTransactionsRebuildingSupported', json_response)
        self.assertIn('areManyInputsSupported', json_response)
        self.assertIn('areManyOutputsSupported', json_response)


if __name__ == '__main__':
    unittest.main()
