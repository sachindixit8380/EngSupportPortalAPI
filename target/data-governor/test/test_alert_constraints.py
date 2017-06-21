"""Tests for the alert_constraints endpoint"""

import json
from mock import patch, Mock

from endpoints import app
from endpoints.alert_constraints import AlertConstraintsEndpoint
from test.test_base import EbeeEndpointTest

app.config['NITEOWL_API_BASE'] = 'https://some_url'
app.config['NITEOWL_LDAP_USER'] = 'some_user'
app.config['NITEOWL_LDAP_PASSWORD'] = 'super_secret'
app.testing = True

class AlertConstraintsTest(EbeeEndpointTest):

    def setUp(self):
        super(AlertConstraintsTest, self).setUp()

        self.requests_patcher = patch('utils.niteowl_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()

    @patch('flask.templating._render')
    def test_valid_get_method(self, mock_render):
        fake_constraint = {'category': 'foo',
                           'categoryKey': 1234,
                           'value': 'baz'}
        headers = self.ebee_delegation_headers

        self.mock_requests.get.return_value = mock_resp(200, {'response': [fake_constraint]})
        self.mock_auth.return_value = 'foo'
        mock_render.return_value = 'some html content'

        response = self.app.get('/alert_constraints')
        assert response.status_code == 200
        self.mock_requests.get.assert_called_with(url='https://some_url/api/alerts/constraint',
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo',
                                                  params=None,
                                                  allow_redirects=True)

    def test_valid_create_constraint(self):
        self.mock_requests.put.return_value = mock_resp(200, {'response': 'some output'})
        self.mock_auth.return_value = 'foo'

        data = {'_method': 'CREATE',
                'category': 'yummy_alerts',
                'value': 'food',
                'job_name': 'test_job',
                'data_source': 'test_data_source'}

        post_data = {'category': 'yummy_alerts',
                     'categoryKey': 1337,
                     'value': 'food'}

        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 302
        self.mock_requests.put.assert_called_with(url='https://some_url/api/alerts/constraint',
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo',
                                                  params=None,
                                                  data=json.dumps(post_data))

    def test_valid_update_constraint(self):
        self.mock_requests.put.return_value = mock_resp(200, {'response': 'some output'})
        self.mock_auth.return_value = 'foo'

        data = {'_method': 'UPDATE',
                'category': 'yummy_alerts',
                'value': 'food',
                'old_value': 'moldy_food',
                'key': 1234}

        post_data = {'category': 'yummy_alerts',
                     'categoryKey': '1234',
                     'value': 'food'}

        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 302
        self.mock_requests.put.assert_called_with(url='https://some_url/api/alerts/constraint',
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo',
                                                  params=None,
                                                  data=json.dumps(post_data))

    def test_valid_delete_constraint(self):
        self.mock_requests.delete.return_value = mock_resp(200, {'response': 'some output'})
        self.mock_auth.return_value = 'foo'

        data = {'_method': 'DELETE',
                'category': 'yummy_alerts',
                'key': 1234}

        headers = self.ebee_delegation_headers
        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 302
        url = 'https://some_url/api/alerts/constraint/category/yummy_alerts/categoryKey/1234'
        self.mock_requests.delete.assert_called_with(url=url,
                                                     headers=headers,
                                                     timeout=15,
                                                     verify=False,
                                                     auth='foo',
                                                     params=None)

    def test_missing_category(self):
        data = {'_method': 'CREATE',
                'value': 'food',
                'job_name': 'test_job',
                'data_source': 'test_data_source'}
        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 400
        assert "Category and value must be specified" in response.data

    def test_missing_value(self):
        data = {'_method': 'CREATE',
                'category': 'yummy_alerts',
                'job_name': 'test_job',
                'data_source': 'test_data_source'}
        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 400
        assert "Category and value must be specified" in response.data

    def test_missing_key_for_update(self):
        data = {'_method': 'UPDATE',
                'category': 'yummy_alerts',
                'value': 'food',
                'old_value': 'moldy_food'}
        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 400
        assert "Key must be specified" in response.data

    def test_missing_job_name_for_create(self):
        data = {'_method': 'CREATE',
                'category': 'yummy_alerts',
                'value': 'food',
                'data_source': 'test_data_source'}
        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 400
        assert "Name and data source must be specified" in response.data

    def test_missing_data_source_for_create(self):
        data = {'_method': 'CREATE',
                'category': 'yummy_alerts',
                'value': 'food',
                'job_name': 'test_job'}
        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 400
        assert "Name and data source must be specified" in response.data

    def test_unsupported_method(self):
        data = {'_method': 'POST',
                'category': 'yummy_alerts',
                'value': 'food',
                'job_name': 'test_job',
                'data_source': 'test_data_source'}
        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 400
        assert "Unsupported method" in response.data

    def test_missing_category_for_delete(self):
        data = {'_method': 'DELETE',
                'key': 1234}
        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 400
        assert "Category and key must be specified" in response.data

    def test_missing_key_for_delete(self):
        data = {'_method': 'DELETE',
                'category': 'yummy_alerts'}
        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 400
        assert "Category and key must be specified" in response.data

    def test_non_existent_job_for_create(self):
        data = {'_method': 'CREATE',
                'category': 'yummy_alerts',
                'value': 'food',
                'job_name': 'not_the_right_name',
                'data_source': 'not_the_right_data_source'}
        response = self.app.post('/alert_constraints', data=data)
        assert response.status_code == 400
        assert "No job exists with given name and data source" in response.data

def mock_resp(code, data):
    mock_resp = Mock()
    mock_resp.status_code = code
    mock_resp.json.return_value = data
    return mock_resp
