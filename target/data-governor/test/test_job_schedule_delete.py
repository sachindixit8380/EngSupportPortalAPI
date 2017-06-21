"""Tests for the job_delete endpoint"""

from mock import patch, Mock

from endpoints import app
from endpoints.job_schedule_delete import JobScheduleDelete
from test.test_base import EbeeEndpointTest

app.config['EBEE_API_BASE'] = 'https://some_url'

class JobScheduleDeleteTest(EbeeEndpointTest):

    def setUp(self):
        super(JobScheduleDeleteTest, self).setUp()

        self.requests_patcher = patch('utils.ebee_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()

    def tearDown(self):
        self.requests_patcher.stop()
        self.auth_patcher.stop()
        super(JobScheduleDeleteTest, self).tearDown()

    @patch('endpoints.job_schedule_delete.url_for')
    @patch('endpoints.job_schedule_delete.get_job_schedule_count')
    def test_valid_delete(self, mock_get_job_schedule_count, mock_url_for):
        job_data = {'name': 'matrix',
                    'data_source': 'zz_top'}
        self.mock_requests.delete.return_value = mock_resp(200, 'some output')
        self.mock_auth.return_value = 'foo'
        mock_get_job_schedule_count.return_value = 2

        headers = self.ebee_delegation_headers
        response = self.app.post('/job_schedule_delete', data=job_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        self.mock_requests.delete.assert_called_with(url='https://some_url/jobs/matrix/schedules/zz_top',
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
