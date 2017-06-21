import json
import datetime
from mock import patch, Mock

from endpoints.job_rule import JobRuleEndpoint
from endpoints import app
from endpoints.database import db, DMFBase, JobSchedule
from test.test_base import EbeeEndpointTest

app.config['EBEE_API_BASE'] = 'https://some_url'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class JobRuleTest(EbeeEndpointTest):

    def setUp(self):
        super(JobRuleTest, self).setUp()

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        self.flask_app = app
        session = db.session()

        self.valid_data = {'job_id': 271828,
                           'table_name': 'foo',
                           'data_source': 'west_village',
                           'load_threshold': 1,
                           'hour_offset': 0,
                           'require_closed_hour': 0}

        self.requests_patcher = patch('utils.ebee_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()

        try:
            job_schedule_entry = JobSchedule(
                id=271828,
                job_name='dan_dan',
                description='',
                min_time_passed=70,
                priority=42,
                active=1,
                bypass_validation=0,
                min_minutes_between_runs=None,
                lastupd=datetime.datetime.utcfromtimestamp(555638400),
                close_hour=1,
                host_to_run_on='12th_and_3rd',
                data_source='east_village',
                reprocess=1,
                paused_until=datetime.datetime.utcfromtimestamp(0),
                first_eligible_hour=datetime.datetime.utcfromtimestamp(10))

            db.session.add(job_schedule_entry)
            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()

    def tearDown(self):
        self.requests_patcher.stop()
        self.auth_patcher.stop()
        DMFBase.metadata.drop_all(db.engine)
        super(JobRuleTest, self).tearDown()

    @patch('endpoints.job_rule.url_for')
    def test_valid_post(self, mock_url_for):
        self.mock_requests.post.return_value = mock_resp(201, 'some_response')
        self.mock_auth.return_value = 'foo'

        boolean_require = True if self.valid_data['require_closed_hour'] else False
        payload = {'dependencyName': self.valid_data['table_name'],
                   'dependencyDataSource': self.valid_data['data_source'],
                   'loadThreshold': self.valid_data['load_threshold'],
                   'hourOffset': self.valid_data['hour_offset'],
                   'requireClosedHour': boolean_require}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/job_rule', data=self.valid_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        url = 'https://some_url/jobs/dan_dan/schedules/east_village/dependencies'
        self.mock_requests.post.assert_called_with(url=url,
                                                   data=json.dumps(payload),
                                                   headers=headers,
                                                   timeout=15,
                                                   verify=False,
                                                   auth='foo',
                                                   params=None)

    @patch('endpoints.job_rule.url_for')
    def test_valid_put(self, mock_url_for):
        self.valid_data['_method'] = 'PUT'
        self.mock_requests.put.return_value = mock_resp(200, 'some_response')
        self.mock_auth.return_value = 'foo'

        boolean_require = True if self.valid_data['require_closed_hour'] else False
        payload = {'dependencyName': self.valid_data['table_name'],
                   'dependencyDataSource': self.valid_data['data_source'],
                   'loadThreshold': self.valid_data['load_threshold'],
                   'hourOffset': self.valid_data['hour_offset'],
                   'requireClosedHour': boolean_require}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/job_rule', data=self.valid_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        url = 'https://some_url/jobs/dan_dan/schedules/east_village/dependencies/foo/dataSources/west_village'
        self.mock_requests.put.assert_called_with(url=url,
                                                   data=json.dumps(payload),
                                                   headers=headers,
                                                   timeout=15,
                                                   verify=False,
                                                   auth='foo')

    @patch('endpoints.job_rule.url_for')
    def test_valid_delete(self, mock_url_for):
        delete_data = {'_method': 'DELETE',
                       'job_id': 271828,
                       'dependency_table_name': 'foo_baz',
                       'dependency_data_source': 'west_village'}
        self.mock_requests.delete.return_value = mock_resp(200, 'some_response')
        self.mock_auth.return_value = 'foo'

        headers = self.ebee_delegation_headers
        response = self.app.post('/job_rule', data=delete_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        url = 'https://some_url/jobs/dan_dan/schedules/east_village/dependencies/foo_baz/dataSources/west_village'
        self.mock_requests.delete.assert_called_with(url=url,
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
