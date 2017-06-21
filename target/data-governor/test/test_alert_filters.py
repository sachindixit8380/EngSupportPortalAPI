"""Tests for the alert_filters endpoint"""

import datetime
import json
from mock import patch, Mock

from endpoints import app
from endpoints.alert_filters import AlertFiltersEndpoint
from test.test_base import EbeeEndpointTest

app.config['NITEOWL_API_BASE'] = 'https://some_url'
app.config['NITEOWL_LDAP_USER'] = 'some_user'
app.config['NITEOWL_LDAP_PASSWORD'] = 'super_secret'
app.testing = True

class AlertFiltersTest(EbeeEndpointTest):

    def setUp(self):
        super(AlertFiltersTest, self).setUp()

        self.requests_patcher = patch('utils.niteowl_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()

    @patch('flask.templating._render')
    def test_valid_get_method(self, mock_render):
        headers = self.ebee_delegation_headers

        self.mock_requests.get.return_value = mock_resp(200, {'response': 'some output'})
        self.mock_auth.return_value = 'foo'
        mock_render.return_value = 'some html content'

        response = self.app.get('/alert_filters')
        assert response.status_code == 200
        self.mock_requests.get.assert_called_with(url='https://some_url/api/alerts/filter',
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo',
                                                  params=None,
                                                  allow_redirects=True)

    @patch('endpoints.alert_filters.datetime')
    def test_valid_create_filter(self, mock_datetime):
        self.mock_requests.post.return_value = mock_resp(200, {'response': 'some output'})
        self.mock_auth.return_value = 'foo'
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2016, 1, 1, 18, 30, 0, 0)
        mock_datetime.timedelta.return_value = datetime.timedelta(minutes=60)

        data = {'action': 'jump!',
                'minutes': 60,
                'keys': ['alert_service', 'category'],
                'values': ['cool_service', 'cool_category'],
                'regex': ['False', 'False']}

        criteria_list = [{'key': 'alert_service', 'value': 'cool_service', 'regex': False},
                         {'key': 'category', 'value': 'cool_category', 'regex': False}]
        criteria = {'criteria': criteria_list}

        post_data = {'criteria': json.dumps(criteria),
                     'action': 'jump!',
                     'until': '2016-01-01 19:30:00'}

        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 302
        self.mock_requests.post.assert_called_with(url='https://some_url/api/alerts/filter',
                                                   headers=headers,
                                                   timeout=15,
                                                   verify=False,
                                                   auth='foo',
                                                   params=None,
                                                   data=json.dumps(post_data))

    @patch('endpoints.alert_filters.datetime')
    def test_valid_update_filter(self, mock_datetime):
        self.mock_requests.put.return_value = mock_resp(200, {'response': 'some output'})
        self.mock_auth.return_value = 'foo'
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2016, 1, 1, 18, 30, 0, 0)
        mock_datetime.timedelta.return_value = datetime.timedelta(minutes=60)

        data = {'_method': 'PUT',
                'minutes': 60,
                'id': 1234}

        put_data = {'until': '2016-01-01 19:30:00'}

        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 302
        self.mock_requests.put.assert_called_with(url='https://some_url/api/alerts/filter/id/1234',
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo',
                                                  params=None,
                                                  data=json.dumps(put_data))

    def test_missing_action_on_create(self):
        data = {'minutes': 60,
                'keys': ['alert_service', 'category'],
                'values': ['cool_service', 'cool_category'],
                'regex': ['False', 'False']}
        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 400
        assert "Please select an action" in response.data

    def test_missing_minutes_on_create(self):
        data = {'action': 'jump!',
                'keys': ['alert_service', 'category'],
                'values': ['cool_service', 'cool_category'],
                'regex': ['False', 'False']}
        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 400
        assert "Please specify how long to set your filter" in response.data

    def test_missing_keys_on_create(self):
        data = {'action': 'jump!',
                'minutes': 60,
                'values': ['cool_service', 'cool_category'],
                'regex': ['False', 'False']}
        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 400
        assert "One or more criteria are missing" in response.data

    def test_missing_values_on_create(self):
        data = {'action': 'jump!',
                'minutes': 60,
                'keys': ['alert_service', 'category'],
                'regex': ['False', 'False']}
        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 400
        assert "One or more criteria are missing" in response.data

    def test_missing_regex_on_create(self):
        data = {'action': 'jump!',
                'minutes': 60,
                'keys': ['alert_service', 'category'],
                'values': ['cool_service', 'cool_category']}
        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 400
        assert "One or more criteria are missing" in response.data

    def test_bad_key_on_create(self):
        data = {'action': 'jump!',
                'minutes': 60,
                'keys': ['alert_service', ''],
                'values': ['cool_service', 'cool_category'],
                'regex': ['False', 'False']}
        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 400
        assert "One or more criteria are missing fields" in response.data

    def test_bad_value_on_create(self):
        data = {'action': 'jump!',
                'minutes': 60,
                'keys': ['alert_service', 'category'],
                'values': ['cool_service', ''],
                'regex': ['False', 'False']}
        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 400
        assert "One or more criteria are missing fields" in response.data

    def test_bad_regex_on_create(self):
        data = {'action': 'jump!',
                'minutes': 60,
                'keys': ['alert_service', 'category'],
                'values': ['cool_service', 'cool_category'],
                'regex': ['False', '']}
        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 400
        assert "One or more criteria are missing fields" in response.data

    def test_missing_minutes_on_update(self):
        data = {'_method': 'PUT',
                'id': 1234}
        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 400
        assert "Minutes and an ID must be specified" in response.data

    def test_missing_id_on_update(self):
        data = {'_method': 'PUT',
                'minutes': 60}
        response = self.app.post('/alert_filters', data=data)
        assert response.status_code == 400
        assert "Minutes and an ID must be specified" in response.data

def mock_resp(code, data):
    mock_resp = Mock()
    mock_resp.status_code = code
    mock_resp.json.return_value = data
    return mock_resp
