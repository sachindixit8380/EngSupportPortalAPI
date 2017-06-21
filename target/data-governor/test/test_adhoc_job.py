"""Tests for the adhoc_job endpoint"""

import json
from mock import patch, Mock

from endpoints import app
from endpoints.adhoc_job import AdhocJob
from endpoints.database import db, DMFBase
from test.test_base import EbeeEndpointTest

app.config['ENV_TO_GSLB_MAP'] = {'sand/nym2': 'appnexus.is.cool'}
app.config['ENV_TO_DATA_SOURCE_MAP'] = {'sand/nym2': 'hadoop_quest'}
app.config['EBEE_API_BASE'] = 'https://some_url'

class AdhocJobTest(EbeeEndpointTest):

    def setUp(self):
        super(AdhocJobTest, self).setUp()

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        session = db.session()

        self.job_data = {'name': 'MITCH2000',
                         'command': '{"yo":"miami"}',
                         'hour': '2015-04-20 04:20:00',
                         'env_to_run_in': 'sand/nym2',
                         'notify_mq': 'okay?',
                         'alert_on_failure': '1',
                         'alert_services': 'food'}

        self.requests_patcher = patch('utils.ebee_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.get_alert_services_patcher = patch('utils.validation_funcs.get_alert_services')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()
        self.mock_get_alert_services = self.get_alert_services_patcher.start()
        self.mock_get_alert_services.return_value = ['food']

    def tearDown(self):
        self.requests_patcher.stop()
        self.auth_patcher.stop()
        self.get_alert_services_patcher.stop()
        DMFBase.metadata.drop_all(db.engine)
        super(AdhocJobTest, self).tearDown()

    def test_valid_job_creation(self):
        valid_output = {'response': {'urls':'https://some_url/processes/adhoc/MITCH2000',
                                     'description':'Job created'}}
        self.mock_requests.post.return_value = mock_resp(201, valid_output)
        self.mock_auth.return_value = 'foo'

        boolean_alert_on_failure = True if self.job_data['alert_on_failure'] else False
        payload = {"name": self.job_data['name'], "jobType": "hadoop_job",
                   "hour": self.job_data['hour'], "dataSource": "hadoop_quest",
                   "dryRun": False, "envToRunIn": self.job_data['env_to_run_in'],
                   "notifyOnMQ": self.job_data['notify_mq'], "alertOnFailure": boolean_alert_on_failure,
                   "alertServices": self.job_data['alert_services']}
        payload["command"] = self.job_data['command']
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/adhoc_job', data=self.job_data)
        self.mock_requests.post.assert_called_with(url='https://some_url/processes/adhoc',
                                                   data=json.dumps(payload),
                                                   headers=headers,
                                                   timeout=15,
                                                   verify=False,
                                                   auth='foo',
                                                   params=None)

    def test_invalid_job_creation(self):
        self.bad_job_data = self.job_data.copy()
        self.bad_job_data["config_file"] = "LOL"
        response = self.app.post('/adhoc_job', data=self.bad_job_data)
        assert response.status_code == 400
        assert "Can only execute artifact, artifact + config_file, config_file, or command." in response.data

def mock_resp(code, data):
    mock_resp = Mock()
    mock_resp.status_code = code
    mock_resp.json.return_value = data
    return mock_resp
