"""Tests for the job_schedule_create endpoint using mock to avoid url_for errors"""

import json
from mock import patch, Mock

from endpoints import app
from endpoints.job_schedule_create import JobScheduleCreate
from endpoints.database import db, DMFBase, DataSources
from test.test_base import EbeeEndpointTest

app.config['ENV_TO_GSLB_MAP'] = {'sand/nym2': 'agg.sand.adnxs.net'}
app.config['EBEE_API_BASE'] = 'https://some_url'
app.testing = True

class JobScheduleCreateTest(EbeeEndpointTest):

    def setUp(self):
        super(JobScheduleCreateTest, self).setUp()

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        session = db.session()

        self.job_schedule_data = {'name': 'foo_bar',
                                  'job_type': 'garbage',
                                  'min_time_passed': 75,
                                  'priority': 3,
                                  'active': 0,
                                  'min_minutes_between_runs': 0,
                                  'close_hour': 1,
                                  'env_to_run_in': 'sand/nym2',
                                  'data_source': 'hadoop_cypress',
                                  'concurrency': 1,
                                  'reprocess': 1,
                                  'pause_for': 0,
                                  'first_eligible_hour': '1970-01-01 10:00:00',
                                  'resource_queue': 'p2',
                                  'alert_svcs': 'poo',
                                  'dep_names': ['wut'],
                                  'dep_data_sources': ['hadoop_cypress']}

        self.dynamic_sync_data = {'origin': 'hadoop_quest',
                                  'origin_table': 'la_mesa',
                                  'destination_table': 'qwerty',
                                  'date_column': 'ymdh'}

        self.requests_patcher = patch('utils.ebee_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.get_alert_services_patcher = patch('utils.validation_funcs.get_alert_services')
        self.get_data_sources_patcher = patch('utils.validation_funcs.get_data_sources')
        self.get_job_type_patcher = patch('endpoints.job_schedule_create.get_job_type_from_job_name')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()
        self.mock_get_alert_services = self.get_alert_services_patcher.start()
        self.mock_get_alert_services.return_value = ['poo']
        self.mock_get_data_sources = self.get_data_sources_patcher.start()
        self.mock_get_data_sources.return_value = ['hadoop_cypress', 'hadoop_quest', 'tupac']
        self.mock_get_job_type = self.get_job_type_patcher.start()
        self.mock_get_job_type.job_type.return_value = 'agg'

        try:
            data_source_entry = DataSources(name='hadoop_cypress')
            data_source_entry_1 = DataSources(name='hadoop_quest')
            db.session.add(data_source_entry)
            db.session.add(data_source_entry_1)
            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()

    def tearDown(self):
        self.requests_patcher.stop()
        self.auth_patcher.stop()
        self.get_alert_services_patcher.stop()
        self.get_data_sources_patcher.stop()
        self.get_job_type_patcher.stop()
        DMFBase.metadata.drop_all(db.engine)
        super(JobScheduleCreateTest, self).tearDown()

    @patch('endpoints.job_schedule_create.url_for')
    def test_valid_job_schedule_creation(self, mock_url_for):
        self.mock_requests.post.return_value = mock_resp(201, 'some output')
        self.mock_auth.return_value = 'foo'

        boolean_active = True if self.job_schedule_data['active'] else False
        boolean_close_hour = True if self.job_schedule_data['close_hour'] else False
        boolean_reprocess = True if self.job_schedule_data['reprocess'] else False
        dep_payload = [{"dependencyName": "wut",
                        "dependencyDataSource": "hadoop_cypress",
                        "loadThreshold": 0,
                        "hourOffset": 0,
                        "requireClosedHour": True}]
        payload = {'executionDelay':self.job_schedule_data['min_time_passed'],
                   'priority':self.job_schedule_data['priority'],
                   'active':boolean_active,
                   'minimumDelay':self.job_schedule_data['min_minutes_between_runs'],
                   'closeHour':boolean_close_hour,
                   'envToRunIn':self.job_schedule_data['env_to_run_in'],
                   'dataSource':self.job_schedule_data['data_source'],
                   'concurrency':self.job_schedule_data['concurrency'],
                   'reprocess':boolean_reprocess,
                   'pausedUntil':'1970-01-01 00:00:01',
                   'firstEligibleHour':self.job_schedule_data['first_eligible_hour'],
                   'resource':self.job_schedule_data['resource_queue'],
                   'alertSvcs':self.job_schedule_data['alert_svcs'],
                   'dependencies':dep_payload,
                   'conflicts':[]}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/job_schedule_create', data=self.job_schedule_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_filter', filter='foo_bar')
        self.mock_requests.post.assert_called_with(url='https://some_url/jobs/foo_bar/schedules',
                                                   data=json.dumps(payload),
                                                   headers=headers,
                                                   timeout=15,
                                                   verify=False,
                                                   auth='foo',
                                                   params=None)

    @patch('endpoints.job_schedule_create.url_for')
    def test_valid_dynamic_sync_job_schedule_creation(self, mock_url_for):
        self.mock_requests.post.return_value = mock_resp(201, 'some output')
        self.mock_auth.return_value = 'foo'

        boolean_active = True if self.job_schedule_data['active'] else False
        boolean_close_hour = True if self.job_schedule_data['close_hour'] else False
        boolean_reprocess = True if self.job_schedule_data['reprocess'] else False
        dep_payload = [{"dependencyName": "wut",
                        "dependencyDataSource": "hadoop_cypress",
                        "loadThreshold": 0,
                        "hourOffset": 0,
                        "requireClosedHour": True}]
        payload = {'executionDelay':self.job_schedule_data['min_time_passed'],
                   'priority':self.job_schedule_data['priority'],
                   'active':boolean_active,
                   'minimumDelay':self.job_schedule_data['min_minutes_between_runs'],
                   'closeHour':boolean_close_hour,
                   'envToRunIn':self.job_schedule_data['env_to_run_in'],
                   'dataSource':self.job_schedule_data['data_source'],
                   'concurrency':self.job_schedule_data['concurrency'],
                   'reprocess':boolean_reprocess,
                   'pausedUntil':'1970-01-01 00:00:01',
                   'firstEligibleHour':self.job_schedule_data['first_eligible_hour'],
                   'resource':self.job_schedule_data['resource_queue'],
                   'alertSvcs':self.job_schedule_data['alert_svcs'],
                   'dependencies':dep_payload,
                   'conflicts':[]}

        dynamic_sync_data = {'origin':self.dynamic_sync_data['origin'],
                             'originTable':self.dynamic_sync_data['origin_table'],
                             'destinationTable':self.dynamic_sync_data['destination_table'],
                             'dateColumn':self.dynamic_sync_data['date_column']}
        payload['dynamicSync'] = dynamic_sync_data
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        self.job_schedule_data.update(self.dynamic_sync_data)
        response = self.app.post('/job_schedule_create', data=self.job_schedule_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_filter', filter='foo_bar')
        self.mock_requests.post.assert_called_with(url='https://some_url/jobs/foo_bar/schedules',
                                                   data=json.dumps(payload),
                                                   headers=headers,
                                                   timeout=15,
                                                   verify=False,
                                                   auth='foo',
                                                   params=None)

    def test_missing_min_time_passed(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['min_time_passed'] = None
        response = self.app.post('/job_schedule_create', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter a min_time_passed, even if it's 0" in response.data

    def test_missing_priority(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['priority'] = None
        response = self.app.post('/job_schedule_create', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter a priority for your job schedule" in response.data

    def test_missing_concurrency(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['concurrency'] = None
        response = self.app.post('/job_schedule_create', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter a concurrency for your job schedule" in response.data

    def test_missing_resource_queue(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['resource_queue'] = None
        response = self.app.post('/job_schedule_create', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter a resource_queue for your job schedule" in response.data

    def test_missing_env_to_run_in(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['env_to_run_in'] = None
        response = self.app.post('/job_schedule_create', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter an env_to_run_in" in response.data

def mock_resp(code, data):
    mock_resp = Mock()
    mock_resp.status_code = code
    mock_resp.json.return_value = data
    return mock_resp
