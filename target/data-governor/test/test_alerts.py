"""Tests for the alerts endpoint"""

from mock import patch, Mock

from endpoints import app
from endpoints.alerts import AlertsEndpoint
from test.test_base import EbeeEndpointTest

app.config['NITEOWL_API_BASE'] = 'https://some_url'
app.config['NITEOWL_LDAP_USER'] = 'some_user'
app.config['NITEOWL_LDAP_PASSWORD'] = 'super_secret'
app.testing = True

class AlertsTest(EbeeEndpointTest):

    def setUp(self):
        super(AlertsTest, self).setUp()

        self.requests_patcher = patch('utils.niteowl_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()

    @patch('flask.templating._render')
    def test_valid_get_method(self, mock_render):
        fake_alert = {'alertService': 'foo'}
        headers = self.ebee_delegation_headers

        self.mock_requests.get.return_value = mock_resp(200, {'response': [fake_alert]})
        self.mock_auth.return_value = 'foo'
        mock_render.return_value = 'some html content'

        response = self.app.get('/alerts')
        assert response.status_code == 200
        self.mock_requests.get.assert_called_with(url='https://some_url/api/alerts/alert',
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo',
                                                  params=None,
                                                  allow_redirects=True)

    def test_valid_clear_single_alert(self):
        self.mock_requests.put.return_value = mock_resp(200, {'response': 'some output'})
        self.mock_auth.return_value = 'foo'

        data = {'_method': 'PUT',
                'alert_id': 1234}

        params = {'id': '1234'}
        headers = self.ebee_delegation_headers

        response = self.app.post('/alerts', data=data)
        assert response.status_code == 302
        self.mock_requests.put.assert_called_with(url='https://some_url/api/alerts/clear',
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo',
                                                  params=params,
                                                  data=None)

    def test_valid_clear_entire_service(self):
        self.mock_requests.put.return_value = mock_resp(200, {'response': 'some output'})
        self.mock_auth.return_value = 'foo'

        data = {'_method': 'PUT',
                'service': 'plz_alert_me'}

        params = {'service': 'plz_alert_me'}
        headers = self.ebee_delegation_headers

        response = self.app.post('/alerts', data=data)
        assert response.status_code == 302
        self.mock_requests.put.assert_called_with(url='https://some_url/api/alerts/clear',
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo',
                                                  params=params,
                                                  data=None)

    def test_missing_id_and_service(self):
        data = {'_method': 'PUT'}
        response = self.app.post('/alerts', data=data)
        assert response.status_code == 400
        assert "Either id or service must be specified" in response.data

    def test_unsupported_method(self):
        data = {'service': 'plz_alert_me'}
        response = self.app.post('/alerts', data=data)
        assert response.status_code == 400
        assert "Unsupported method" in response.data

def mock_resp(code, data):
    mock_resp = Mock()
    mock_resp.status_code = code
    mock_resp.json.return_value = data
    return mock_resp
