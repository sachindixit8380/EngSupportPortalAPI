"""Tests for the schedule_job endpoint"""

import json
from mock import patch, Mock

from endpoints import app
from endpoints.schedule_job import ScheduleJob
from endpoints.database import db, DMFBase, DataSources
from test.test_base import EbeeEndpointTest

app.config['ENV_TO_GSLB_MAP'] = {'sand/nym2': 'agg.sand.adnxs.net'}
app.config['EBEE_API_BASE'] = 'https://some_url'
app.testing = True

class ScheduleJobTest(EbeeEndpointTest):

    def setUp(self):
        super(ScheduleJobTest, self).setUp()

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        session = db.session()

        self.job_data = {'name': 'matrix',
                         'job_type': 'sync',
                         'config_info': 'config',
                         'config_file': 'there_is_no.spoon',
                         'time_interval': 'hour',
                         'description': 'the_one',
                         'group_name': 'dpaas_data_team',
                         'min_time_passed': 75,
                         'priority': 3,
                         'active': 0,
                         'min_minutes_between_runs': 0,
                         'close_hour': 1,
                         'env_to_run_in': 'sand/nym2',
                         'data_source': 'test_data_source',
                         'concurrency': 1,
                         'reprocess': 1,
                         'pause_for': 0,
                         'first_eligible_hour': '1970-01-01 10:00:00',
                         'resource_queue': 'p2',
                         'alert_svcs': 'poo',
                         'dep_names': ['hello', 'world'],
                         'dep_data_sources': ['hadoop_quest', 'hadoop_cypress']}

        self.dynamic_sync_data = {'origin': 'test_data_source',
                                  'origin_table': 'la_mesa',
                                  'destination_table': 'qwerty',
                                  'date_column': 'ymdh'}

        self.requests_patcher = patch('utils.ebee_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.get_alert_services_patcher = patch('endpoints.globals.get_alert_services')
        self.valid_alert_services_patcher = patch('utils.validation_funcs.get_alert_services')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()
        self.mock_get_alert_services = self.get_alert_services_patcher.start()
        self.mock_get_alert_services.return_value = ['poo']
        self.mock_valid_alert_services = self.valid_alert_services_patcher.start()
        self.mock_valid_alert_services.return_value = ['poo']

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
        self.valid_alert_services_patcher.stop()
        DMFBase.metadata.drop_all(db.engine)
        super(ScheduleJobTest, self).tearDown()

    @patch('endpoints.schedule_job.url_for')
    def test_valid_job_creation(self, mock_url_for):
        self.mock_requests.post.return_value = mock_resp(201, 'some output')
        self.mock_auth.return_value = 'foo'

        boolean_active = True if self.job_data['active'] else False
        boolean_close_hour = True if self.job_data['close_hour'] else False
        boolean_reprocess = True if self.job_data['reprocess'] else False

        dep_payload = [{'dependencyName':self.job_data['dep_names'][0],
                        'dependencyDataSource':self.job_data['dep_data_sources'][0],
                        'loadThreshold':0,
                        'hourOffset':0,
                        'requireClosedHour':boolean_close_hour},
                        {'dependencyName':self.job_data['dep_names'][1],
                        'dependencyDataSource':self.job_data['dep_data_sources'][1],
                        'loadThreshold':0,
                        'hourOffset':0,
                        'requireClosedHour':boolean_close_hour}]
        schedule_payload = {'executionDelay':self.job_data['min_time_passed'],
                            'priority':self.job_data['priority'],
                            'active':boolean_active,
                            'minimumDelay':self.job_data['min_minutes_between_runs'],
                            'closeHour':boolean_close_hour,
                            'envToRunIn':self.job_data['env_to_run_in'],
                            'dataSource':self.job_data['data_source'],
                            'concurrency':self.job_data['concurrency'],
                            'reprocess':boolean_reprocess,
                            'firstEligibleHour':self.job_data['first_eligible_hour'],
                            'alertSvcs':self.job_data['alert_svcs'],
                            'pausedUntil':'1970-01-01 00:00:01',
                            'resource':self.job_data['resource_queue'],
                            'dependencies':dep_payload,
                            'conflicts':[]}
        payload = {'name':self.job_data['name'],
                   'jobType':self.job_data['job_type'],
                   'configFile':self.job_data['config_file'],
                   'timeInterval':self.job_data['time_interval'],
                   'description':self.job_data['description'],
                   'groupName':self.job_data['group_name'],
                   'schedules':[schedule_payload]}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/schedule_job', data=self.job_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_filter',
                                        filter=payload['name'],
                                        data_source=schedule_payload['dataSource'])
        self.mock_requests.post.assert_called_with(url='https://some_url/jobs',
                                                   data=json.dumps(payload),
                                                   headers=headers,
                                                   timeout=15,
                                                   verify=False,
                                                   auth='foo',
                                                   params=None)

    @patch('endpoints.schedule_job.url_for')
    def test_valid_dynamic_sync_creation(self, mock_url_for):
        self.mock_requests.post.return_value = mock_resp(201, 'some output')
        self.mock_auth.return_value = 'foo'

        self.job_data['job_type'] = 'dynamic_sync'
        self.job_data.update(self.dynamic_sync_data)

        boolean_active = True if self.job_data['active'] else False
        boolean_close_hour = True if self.job_data['close_hour'] else False
        boolean_reprocess = True if self.job_data['reprocess'] else False

        dep_payload = [{'dependencyName':self.job_data['dep_names'][0],
                        'dependencyDataSource':self.job_data['dep_data_sources'][0],
                        'loadThreshold':0,
                        'hourOffset':0,
                        'requireClosedHour':boolean_close_hour},
                        {'dependencyName':self.job_data['dep_names'][1],
                        'dependencyDataSource':self.job_data['dep_data_sources'][1],
                        'loadThreshold':0,
                        'hourOffset':0,
                        'requireClosedHour':boolean_close_hour}]
        schedule_payload = {'executionDelay':self.job_data['min_time_passed'],
                            'priority':self.job_data['priority'],
                            'active':boolean_active,
                            'minimumDelay':self.job_data['min_minutes_between_runs'],
                            'closeHour':boolean_close_hour,
                            'envToRunIn':self.job_data['env_to_run_in'],
                            'dataSource':self.job_data['data_source'],
                            'concurrency':self.job_data['concurrency'],
                            'reprocess':boolean_reprocess,
                            'firstEligibleHour':self.job_data['first_eligible_hour'],
                            'alertSvcs':self.job_data['alert_svcs'],
                            'pausedUntil':'1970-01-01 00:00:01',
                            'resource':self.job_data['resource_queue'],
                            'dependencies':dep_payload,
                            'conflicts':[]}
        dynamic_sync_data = {'origin':self.job_data['origin'],
                             'originTable':self.job_data['origin_table'],
                             'destinationTable':self.job_data['destination_table'],
                             'dateColumn':self.job_data['date_column']}
        schedule_payload['dynamicSync'] = dynamic_sync_data
        payload = {'name':self.job_data['name'],
                   'jobType':self.job_data['job_type'],
                   'configFile':self.job_data['config_file'],
                   'timeInterval':self.job_data['time_interval'],
                   'description':self.job_data['description'],
                   'groupName':self.job_data['group_name'],
                   'schedules':[schedule_payload]}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/schedule_job', data=self.job_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_filter',
                                        filter=payload['name'],
                                        data_source=schedule_payload['dataSource'])
        self.mock_requests.post.assert_called_with(url='https://some_url/jobs',
                                                   data=json.dumps(payload),
                                                   headers=headers,
                                                   timeout=15,
                                                   verify=False,
                                                   auth='foo',
                                                   params=None)

    def test_missing_name(self):
        invalid_data = self.job_data.copy()
        invalid_data['name'] = None
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter a name for your job" in response.data

    def test_missing_job_type(self):
        invalid_data = self.job_data.copy()
        invalid_data['job_type'] = None
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter a job_type" in response.data

    def test_missing_config_file(self):
        invalid_data = self.job_data.copy()
        invalid_data['config_file'] = None
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Please specify a config_file for your job" in response.data


    def test_invalid_name(self):
        invalid_data = self.job_data.copy()
        invalid_data['name'] = 'ha ha ha'
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Please remove all spaces from the name" in response.data

    def test_invalid_job_type(self):
        invalid_data = self.job_data.copy()
        invalid_data['job_type'] = 'random_job'
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Invalid job_type" in response.data

    def test_invalid_config_file(self):
        invalid_data = self.job_data.copy()
        invalid_data['config_file'] = 'meep moop'
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Please remove all spaces from the config_file" in response.data

    def test_invalid_time_interval(self):
        invalid_data = self.job_data.copy()
        invalid_data['time_interval'] = 'monthly'
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "The only acceptable values for the time_interval field are 'hour' and 'day'" in response.data

    def test_missing_min_time_passed(self):
        invalid_data = self.job_data.copy()
        invalid_data['min_time_passed'] = None
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter a min_time_passed, even if it's 0" in response.data

    def test_missing_priority(self):
        invalid_data = self.job_data.copy()
        invalid_data['priority'] = None
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter a priority for your job schedule" in response.data

    def test_missing_concurrency(self):
        invalid_data = self.job_data.copy()
        invalid_data['concurrency'] = None
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter a concurrency for your job schedule" in response.data

    def test_missing_resource_queue(self):
        invalid_data = self.job_data.copy()
        invalid_data['resource_queue'] = None
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter a resource_queue for your job schedule" in response.data

    def test_missing_env_to_run_in(self):
        invalid_data = self.job_data.copy()
        invalid_data['env_to_run_in'] = None
        response = self.app.post('/schedule_job', data=invalid_data)
        assert response.status_code == 400
        assert "Please enter an env_to_run_in" in response.data

def mock_resp(code, data):
    mock_resp = Mock()
    mock_resp.status_code = code
    mock_resp.json.return_value = data
    return mock_resp
