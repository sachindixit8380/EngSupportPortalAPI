"""Tests for the job_delete endpoint"""

from mock import patch, Mock

from endpoints import app
from endpoints.job_delete import JobDelete
from test.test_base import EbeeEndpointTest

app.config['EBEE_API_BASE'] = 'https://some_url'

class JobDeleteTest(EbeeEndpointTest):

    def setUp(self):
        super(JobDeleteTest, self).setUp()

        self.requests_patcher = patch('utils.ebee_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()

    def tearDown(self):
        self.requests_patcher.stop()
        self.auth_patcher.stop()
        super(JobDeleteTest, self).tearDown()

    @patch('endpoints.job_delete.url_for')
    def test_valid_delete(self, mock_url_for):
        job_data = {'name': 'matrix'}
        self.mock_requests.delete.return_value = mock_resp(200, 'some output')
        self.mock_auth.return_value = 'foo'

        headers = self.ebee_delegation_headers
        response = self.app.post('/job_delete', data=job_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        self.mock_requests.delete.assert_called_with(url='https://some_url/jobs/matrix',
                                                     timeout=15,
                                                     verify=False,
                                                     auth='foo',
                                                     params=None,
                                                     headers=headers)

def mock_resp(code, data):
    mock_resp = Mock()
    mock_resp.status_code = code
    mock_resp.json.return_value = data
    return mock_resp
