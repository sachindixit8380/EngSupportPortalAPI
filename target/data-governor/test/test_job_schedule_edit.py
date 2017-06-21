"""Tests for the job_schedule_edit endpoint"""

import json
from mock import patch, Mock, call

from endpoints.job_schedule_edit import JobScheduleEdit
from endpoints import app
from endpoints.database import db, DMFBase, DataSources
from test.test_base import EbeeEndpointTest

app.config['EBEE_API_BASE'] = 'https://some_url'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['ENV_TO_GSLB_MAP'] = {'sand/nym2': 'agg.sand.adnxs.net'}
app.testing = True

class JobScheduleEditTest(EbeeEndpointTest):

    def setUp(self):
        super(JobScheduleEditTest, self).setUp()

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        session = db.session()

        self.job_schedule_data = {'job_name': 'foo_bar',
                                  'job_data_source': 'hadoop_cypress',
                                  'job_type': 'agg',
                                  'min_time_passed': 75,
                                  'old_priority': 2,
                                  'priority': 3,
                                  'active': 0,
                                  'min_minutes_between_runs': 0,
                                  'close_hour': 1,
                                  'env_to_run_in': 'sand/nym2',
                                  'data_source': 'test_data_source',
                                  'concurrency': 1,
                                  'reprocess': 1,
                                  'paused_until': '1980-02-02 20:00:00',
                                  'first_eligible_hour': '1970-01-01 10:00:00',
                                  'resource_queue': 'p2',
                                  'alert_svcs': 'poo',
                                  'edit_reason': 'whatever'}

        self.dyn_sync_data = {'job_name': 'foo_bar',
                              'job_data_source': 'hadoop_cypress',
                              'job_type': 'dynamic_sync',
                              'dyn_sync_origin': 'test_data_source',
                              'dyn_sync_origin_table': 'gob_stop_her',
                              'dyn_sync_dest_table': 'what_is_life',
                              'dyn_sync_date_column': 'ymdh'}

        self.requests_patcher = patch('utils.ebee_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')
        self.url_for_patcher = patch('endpoints.job_schedule_edit.url_for')
        self.get_alert_services_patcher = patch('utils.validation_funcs.get_alert_services')
        self.log_patcher = patch('endpoints.job_schedule_edit.log_job_edits')
        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()
        self.mock_url_for = self.url_for_patcher.start()
        self.mock_get_alert_services = self.get_alert_services_patcher.start()
        self.mock_get_alert_services.return_value = ['poo']
        self.mock_log = self.log_patcher.start()

        try:
            data_source_entry = DataSources(name='hadoop_cypress')
            session.add(data_source_entry)
            session.commit()
        except Exception, e:
            print e
            session.rollback()
            self.tearDown()

    def tearDown(self):
        self.requests_patcher.stop()
        self.auth_patcher.stop()
        self.url_for_patcher.stop()
        self.get_alert_services_patcher.stop()
        self.log_patcher.stop()
        DMFBase.metadata.drop_all(db.engine)
        super(JobScheduleEditTest, self).tearDown()

    @patch('endpoints.job_schedule_edit.url_for')
    def test_valid_edit_with_reason(self, mock_url_for):
        self.mock_requests.put.return_value = mock_resp(200, 'some output')
        self.mock_auth.return_value = 'foo'

        boolean_active = True if self.job_schedule_data['active'] else False
        boolean_close_hour = True if self.job_schedule_data['close_hour'] else False
        boolean_reprocess = True if self.job_schedule_data['reprocess'] else False
        payload = {'executionDelay':self.job_schedule_data['min_time_passed'],
                   'priority':self.job_schedule_data['priority'],
                   'active':boolean_active,
                   'minimumDelay':self.job_schedule_data['min_minutes_between_runs'],
                   'closeHour':boolean_close_hour,
                   'envToRunIn':self.job_schedule_data['env_to_run_in'],
                   'concurrency':self.job_schedule_data['concurrency'],
                   'reprocess':boolean_reprocess,
                   'pausedUntil':self.job_schedule_data['paused_until'],
                   'firstEligibleHour':self.job_schedule_data['first_eligible_hour'],
                   'resource':self.job_schedule_data['resource_queue'],
                   'alertSvcs':self.job_schedule_data['alert_svcs']}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        self.job_schedule_data['edit_reason'] = 'because why not'
        response = self.app.post('/job_schedule_edit', data=self.job_schedule_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        self.mock_requests.put.assert_called_with(url='https://some_url/jobs/foo_bar/schedules/hadoop_cypress',
                                                  data=json.dumps(payload),
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo')

    @patch('endpoints.job_schedule_edit.url_for')
    def test_valid_edit_with_no_reason(self, mock_url_for):
        self.mock_requests.put.return_value = mock_resp(200, 'some output')
        self.mock_auth.return_value = 'foo'

        boolean_active = True if self.job_schedule_data['active'] else False
        boolean_close_hour = True if self.job_schedule_data['close_hour'] else False
        boolean_reprocess = True if self.job_schedule_data['reprocess'] else False
        payload = {'executionDelay':self.job_schedule_data['min_time_passed'],
                   'priority':self.job_schedule_data['priority'],
                   'active':boolean_active,
                   'minimumDelay':self.job_schedule_data['min_minutes_between_runs'],
                   'closeHour':boolean_close_hour,
                   'envToRunIn':self.job_schedule_data['env_to_run_in'],
                   'concurrency':self.job_schedule_data['concurrency'],
                   'reprocess':boolean_reprocess,
                   'pausedUntil':self.job_schedule_data['paused_until'],
                   'firstEligibleHour':self.job_schedule_data['first_eligible_hour'],
                   'resource':self.job_schedule_data['resource_queue'],
                   'alertSvcs':self.job_schedule_data['alert_svcs']}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/job_schedule_edit', data=self.job_schedule_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        self.mock_requests.put.assert_called_with(url='https://some_url/jobs/foo_bar/schedules/hadoop_cypress',
                                                  data=json.dumps(payload),
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo')

    @patch('endpoints.job_schedule_edit.url_for')
    def test_valid_dyn_sync_edit(self, mock_url_for):
        self.mock_requests.put.return_value = mock_resp(200, 'some output')
        self.mock_auth.return_value = 'foo'

        boolean_active = True if self.job_schedule_data['active'] else False
        boolean_close_hour = True if self.job_schedule_data['close_hour'] else False
        boolean_reprocess = True if self.job_schedule_data['reprocess'] else False
        payload = {'executionDelay':self.job_schedule_data['min_time_passed'],
                   'priority':self.job_schedule_data['priority'],
                   'active':boolean_active,
                   'minimumDelay':self.job_schedule_data['min_minutes_between_runs'],
                   'closeHour':boolean_close_hour,
                   'envToRunIn':self.job_schedule_data['env_to_run_in'],
                   'concurrency':self.job_schedule_data['concurrency'],
                   'reprocess':boolean_reprocess,
                   'pausedUntil':self.job_schedule_data['paused_until'],
                   'firstEligibleHour':self.job_schedule_data['first_eligible_hour'],
                   'resource':self.job_schedule_data['resource_queue'],
                   'alertSvcs':self.job_schedule_data['alert_svcs']}
        payload2 = {'origin':self.dyn_sync_data['dyn_sync_origin'],
                    'originTable':self.dyn_sync_data['dyn_sync_origin_table'],
                    'destinationTable':self.dyn_sync_data['dyn_sync_dest_table'],
                    'dateColumn':self.dyn_sync_data['dyn_sync_date_column']}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        combined_data = self.job_schedule_data.copy()
        combined_data.update(self.dyn_sync_data)
        response = self.app.post('/job_schedule_edit', data=combined_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        expected_calls = [
            call(url='https://some_url/jobs/foo_bar/schedules/hadoop_cypress',
                 data=json.dumps(payload),
                 headers=headers,
                 timeout=15,
                 verify=False,
                 auth='foo'),
            call(url='https://some_url/jobs/foo_bar/schedules/hadoop_cypress/dynamicSyncs',
                 data=json.dumps(payload2),
                 headers=headers,
                 timeout=15,
                 verify=False,
                 auth='foo')
        ]
        self.mock_requests.put.assert_has_calls(expected_calls, any_order=True)

    @patch('endpoints.job_schedule_edit.url_for')
    def test_multiple_job_schedule_edit(self, mock_url_for):
        self.mock_requests.put.return_value = mock_resp(200, 'some output')
        self.mock_auth.return_value = 'foo'

        data = {'_method': 'BULK',
                'job_schedule_ids': ['1', '2', '3'],
                'active': 1,
                'min_time_passed': 45,
                'first_eligible_hour': '2010-01-01 10:00:00',
                'edit_reason': 'some_reason'}
        payload = {'ids': [1, 2, 3],
                   'active': True if data['active'] else False,
                   'executionDelay': 45,
                   'firstEligibleHour': '2010-01-01 10:00:00'}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/job_schedule_edit', data=data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        self.mock_requests.put.assert_called_with(url='https://some_url/jobs/schedules/bulk',
                                                  data=json.dumps(payload),
                                                  headers=headers,
                                                  timeout=15,
                                                  verify=False,
                                                  auth='foo')

    def test_invalid_min_time_passed(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['min_time_passed'] = -20
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "min_time_passed must be a positive integer" in response.data

    def test_string_min_time_passed(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['min_time_passed'] = 'str'
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "Non-integer value for min_time_passed" in response.data

    def test_invalid_priority(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['priority'] = 150
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "priority must be an integer between 0 and 4" in response.data

    def test_string_priority(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['priority'] = 'str'
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "Non-integer value for priority" in response.data

    def test_invalid_active(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['active'] = 5
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "The only acceptable values for active are 1 and 0" in response.data

    def test_invalid_min_minutes_between_runs(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['min_minutes_between_runs'] = -5
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "min_minutes_between_runs must be a positive integer" in response.data

    def test_string_min_minutes_between_runs(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['min_minutes_between_runs'] = 'str'
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "Non-integer value for min_minutes_between_runs" in response.data

    def test_invalid_close_hour(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['close_hour'] = 10
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "The only acceptable values for close_hour are 1 and 0" in response.data

    def test_invalid_env_to_run_in(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['env_to_run_in'] = 'greetings'
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "{0} is not a valid env_to_run_in".format(invalid_data['env_to_run_in']) in response.data

    def test_invalid_env_env_to_run_in(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['env_to_run_in'] = 'dev/nym2'
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "{0} is not a valid env_to_run_in".format(invalid_data['env_to_run_in']) in response.data

    def test_invalid_dc_env_to_run_in(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['env_to_run_in'] = 'prod/sin1'
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "{0} is not a valid env_to_run_in".format(invalid_data['env_to_run_in']) in response.data

    def test_zero_concurrency(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['concurrency'] = 0
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "concurrency must be a positive integer" in response.data

    def test_string_concurrency(self):
        invalid_data = self.job_schedule_data.copy()
        invalid_data['concurrency'] = 'str'
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "Non-integer value for concurrency" in response.data

    def test_invalid_dyn_sync_origin_table(self):
        invalid_data = self.dyn_sync_data.copy()
        invalid_data['dyn_sync_origin_table'] = 'look ma, spaces!'
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "Please remove all spaces from the table_name" in response.data

    def test_invalid_dyn_sync_destination_table(self):
        invalid_data = self.dyn_sync_data.copy()
        invalid_data['dyn_sync_dest_table'] = None
        response = self.app.post('/job_schedule_edit', data=invalid_data)
        assert response.status_code == 400
        assert "Please specify a table_name" in response.data

def mock_resp(code, data):
    mock_resp = Mock()
    mock_resp.status_code = code
    mock_resp.json.return_value = data
    return mock_resp
