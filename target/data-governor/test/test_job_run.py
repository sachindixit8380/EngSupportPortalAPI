"""Tests for the job run endpoint"""
import datetime
from xml.etree import ElementTree
from mock import patch, call

import unittest
from endpoints.job_run import JobRunEndpoint
from test.test_base import EndpointTest
from endpoints import app
from endpoints.database import db, DMFBase, Job, JobSchedule, RunningJob

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class JobRunEndpointTest(EndpointTest):

    def setUp(self):
        super(JobRunEndpointTest, self).setUp()
        self.db = db
        DMFBase.metadata.create_all(db.engine)

        # stage data we'll keep common to all the things, for simplicity
        try:
            running_job_entry = RunningJob(
                id=1234,
                job_id=510,
                hour=datetime.datetime.utcfromtimestamp(555638400),
                name='hey_ma',
                table_name='dipset',
                config_file='come_home_with_me.inc',
                job_type='vtmsync',
                status='processing',
                request="""{"hey ma": "whats up",
                    "lets slide": "all right",
                    "got drops": "got coupes",
                    "got trucks": "got jeeps",
                    "all right": "and we gonna take a ride tonight"
                }""",
                response=None,
                job='hey_ma',
                information="""{"downtown clubbin": "ladies night",
                    "shorty": "crazy right",
                    "approach": "ma whats your age and type",
                    "looked at me laughing": "yous a baby right",
                    "told her": "18 and live a crazy life"
                }""",
                created_on=datetime.datetime.utcfromtimestamp(577670400),
                started_on=datetime.datetime.utcfromtimestamp(577670400),
                completed_on=datetime.datetime.utcfromtimestamp(1),
                data_source='vertica_camron',
                reprocess=1,
                host_ran_on="55.exit.damn.damn.already.we.home")

            job_entry = Job(
                name='hey_ma',
                job_type='vtmsync',
                config_file='come_home_with_me.inc',
                table_name='dipset',
                lastupd=datetime.datetime.utcfromtimestamp(1),
                is_monitored=0,
                time_interval='hour',
                is_system=0,
                description='')

            job_schedule_entry = JobSchedule(
                id=510,
                job_name='hey_ma',
                description='',
                min_time_passed=18,
                priority=55,
                active=1,
                bypass_validation=0,
                min_minutes_between_runs=None,
                lastupd=datetime.datetime.utcfromtimestamp(1),
                close_hour=1,
                env_to_run_in='sand/nym2',
                data_source='vertica_camron',
                reprocess=1,
                paused_until=datetime.datetime.utcfromtimestamp(1))

            db.session.add(running_job_entry)
            db.session.add(job_entry)
            db.session.add(job_schedule_entry)
            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)

    def test_missing_id_returns_error(self):
        response = self.app.get('/job_run')
        assert response.status_code == 400
        assert '[id] is a required field' in response.data

    @patch('endpoints.job_run.datetime')
    def test_privileged_get_for_valid_id_with_process_details_returns_correct_run_data(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime.datetime.utcfromtimestamp(577670405)
        response = self.app.get('/job_run?id=1234')

        # make sure we actually checked perms
        expected_calls = [call('view_job_run_config')]

        assert response.status_code == 200

        html = ElementTree.fromstring(response.data)
        assert html.find('.//*[@class="job_run_id"]').text == '1234'
        assert html.find('.//*[@class="job_run_name"]').text == 'hey_ma'
        assert html.find('.//*[@class="job_config_file"]').text == 'come_home_with_me.inc'
        assert html.find('.//*[@class="job_hour"]').text == '1987-08-11 00:00:00'
        assert html.find('.//*[@class="job_schedule_id"]').text == '510'
        assert html.find('.//*[@class="job_interval"]').text == 'hour'
        assert html.find('.//*[@class="data_source"]').text == 'vertica_camron'
        assert html.find('.//*[@class="job_type"]').text == 'vtmsync'
        assert html.find('.//*[@class="env_to_run_in"]').text == 'sand/nym2'
        assert html.find('.//*[@class="host_ran_on"]').text == '55.exit.damn.damn.already.we.home'
        assert html.find('.//*[@class="started_on"]').text == '1988-04-22 00:00:00'
        assert html.find('.//*[@class="completed_on"]').text == '-'
        assert html.find('.//*[@class="run_time"]').text == '0:00:05*'
        assert html.find('.//*[@class="job_run_status"]').text == 'processing'
        assert 'we gonna take a ride tonight' in html.find('.//*[@class="request"]').text
        assert 'None' in html.find('.//*[@class="response"]').text
        assert '18 and live a crazy life' in html.find('.//*[@class="job_run_information"]').text

    def test_job_not_found(self):
        assert self.app.get('/job_run?id=6345789').status_code == 404

    def test_non_numeric_id_errors_cleanly(self):
        assert self.app.get('/job_run?id=1234a').status_code == 400

    def test_job_config_not_displayed_when_not_permitted(self):
        self.mock_perm_g.user_groups = ["dpaas_unauthorized"]
        response = self.app.get('/job_run?id=1234')

        expected_calls = [call('view_job_run_config')]

        html = ElementTree.fromstring(response.data)
        proc_info = html.find('.//*[@class="process_info"]')
        assert proc_info.find('.//*[@class="job_config"]') == None

        self.mock_perm_g.user_groups = ["dpaas_admin_rw"]

if __name__ == '__main__':
    import unittest
    unittest.main()
