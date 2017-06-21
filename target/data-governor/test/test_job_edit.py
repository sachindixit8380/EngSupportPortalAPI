"""Tests for the job_edit endpoint"""

import json
from mock import patch, Mock

from endpoints.job_edit import JobEdit
from endpoints import app
from endpoints.database import db, DMFBase
from test.test_base import EbeeEndpointTest

app.config['EBEE_API_BASE'] = 'https://some_url'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class JobEditTest(EbeeEndpointTest):

    def setUp(self):
        super(JobEditTest, self).setUp()

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        session = db.session()

        self.job_data = {'job_name': 'matrix',
                         'job_type': 'sync',
                         'config_file': 'there_is_no.spoon',
                         'time_interval': 'hour',
                         'description': 'the_one',
                         'group_name': 'dpaas_data_team',
                         'edit_reason': 'just changing things nbd'}

        self.requests_patcher = patch('utils.ebee_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.log_patcher = patch('endpoints.job_edit.log_job_edits')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()
        self.mock_log = self.log_patcher.start()

    def tearDown(self):
        self.requests_patcher.stop()
        self.auth_patcher.stop()
        self.log_patcher.stop()
        DMFBase.metadata.drop_all(db.engine)
        super(JobEditTest, self).tearDown()

    @patch('endpoints.job_edit.url_for')
    def test_valid_job_edit(self, mock_url_for):
        self.mock_requests.put.return_value = mock_resp(200, 'some output')
        self.mock_auth.return_value = 'foo'

        payload = {'jobType':self.job_data['job_type'],
                   'configFile':self.job_data['config_file'],
                   'timeInterval':self.job_data['time_interval'],
                   'description':self.job_data['description'],
                   'groupName':self.job_data['group_name']}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/job_edit', data=self.job_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        self.mock_requests.put.assert_called_with(url='https://some_url/jobs/{}'.format(self.job_data['job_name']),
                                                  data=json.dumps(payload),
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo')

    def test_missing_name(self):
        invalid_data = self.job_data.copy()
        invalid_data['job_name'] = None
        response = self.app.post('/job_edit', data=invalid_data)
        assert response.status_code == 400
        assert "Missing job_name" in response.data

    def test_invalid_job_type(self):
        invalid_data = self.job_data.copy()
        invalid_data['job_type'] = 'yucky_ducky'
        response = self.app.post('/job_edit', data=invalid_data)
        assert response.status_code == 400
        assert "Invalid job_type" in response.data

    def test_invalid_config_file(self):
        invalid_data = self.job_data.copy()
        invalid_data['config_file'] = 'yo i have spaces'
        response = self.app.post('/job_edit', data=invalid_data)
        assert response.status_code == 400
        assert "Please remove all spaces from the config_file" in response.data

    def test_invalid_time_interval(self):
        invalid_data = self.job_data.copy()
        invalid_data['time_interval'] = 'month'
        response = self.app.post('/job_edit', data=invalid_data)
        assert response.status_code == 400
        assert "The only acceptable values for the time_interval field are 'hour' and 'day'" in response.data

def mock_resp(code, data):
    mock_resp = Mock()
    mock_resp.status_code = code
    mock_resp.json.return_value = data
    return mock_resp
