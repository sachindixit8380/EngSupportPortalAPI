"""Tests for the job run endpoint"""
import datetime
from xml.etree import ElementTree

import unittest
from mock import patch
from endpoints.job_filter import JobFilterEndpoint
from test.test_base import EndpointTest
from endpoints import app
from endpoints.database import db, DMFBase, Job, JobSchedule, RunningJob

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class JobFilterEndpointTest(EndpointTest):

    def setUp(self):
        super(JobFilterEndpointTest, self).setUp()
        self.db = db
        DMFBase.metadata.create_all(db.engine)
        try:
            running_job_entry = RunningJob(
                id=12345,
                job_id=666,
                hour=datetime.datetime.utcfromtimestamp(555638400),
                name='beer_oclock',
                table_name='pre_weekend_fun',
                config_file='drop_off_service.inc',
                job_type='agg',
                status='completed',
                request="""{"happy_hour": "until_8_pm"}""",
                response=None,
                job='beer_oclock',
                information="""{"foo": "bar"}""",
                created_on=datetime.datetime.utcfromtimestamp(555638400),
                started_on=datetime.datetime.utcfromtimestamp(555638401),
                completed_on=datetime.datetime.utcnow(),
                data_source='vertica_camron',
                reprocess=1)

            job_schedule_entry = JobSchedule(
                id=666,
                job_name='beer_oclock',
                description='',
                min_time_passed=666,
                priority=55,
                active=1,
                bypass_validation=0,
                min_minutes_between_runs=None,
                lastupd=datetime.datetime.utcfromtimestamp(1),
                close_hour=1,
                host_to_run_on='01.agg.prod.ewr1',
                data_source='vertica_camron',
                reprocess=1,
                paused_until=datetime.datetime.utcfromtimestamp(1))

            job_entry = Job(
                name = 'beer_oclock',
                job_type = 'agg',
                config_file = 'drop_off_service.inc',
                table_name = 'beer_oclock',
                time_interval = 'hour')

            db.session.add(running_job_entry)
            db.session.add(job_schedule_entry)
            db.session.add(job_entry)
            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)

    def test_does_not_return_non_matching(self):
        response = self.app.get('/job_filter?filter=there_is_no_spoon')
        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        job_ids = html.findall('.//td[@class="job_id"]')
        job_run_ids = html.findall('.//td[@class="job_run_id"]')
        assert len(job_ids) == 0
        assert len(job_run_ids) == 0

    def test_returns_matching(self):
        response = self.app.get('/job_filter?filter=beer_oclock')
        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        job_ids = html.findall('.//*[@class="job_id"]')
        job_run_names = html.findall('.//*[@class="job_run_name"]')
        assert len(job_ids) == 1
        assert job_ids[0].text == '666'
        assert len(job_run_names) == 1
        assert job_run_names[0].text == 'beer_oclock'

    @patch('endpoints.job_filter.get_running_jobs')
    def test_applies_correct_data_source_filter(self, mock_get_running_jobs):
        self.app.get('/job_filter?data_source=vertica_camron')
        mock_get_running_jobs.assert_called_with(data_source='vertica_camron', host_ran_on='', record_count=50, filter_string='', statuses=[], hour=None)

    @patch('endpoints.job_filter.get_running_jobs')
    def test_records_not_limited_when_statuses_is_only_processing(self, mock_get_running_jobs):
        self.app.get('/job_filter?data_source=vertica_camron&status=processing')
        mock_get_running_jobs.assert_called_with(data_source='vertica_camron', host_ran_on='', record_count=None, filter_string='', statuses=['processing'], hour=None)

    @patch('endpoints.job_filter.get_running_jobs')
    def test_applies_correct_host_box_filter(self, mock_get_running_jobs):
        self.app.get('/job_filter?host=05.agg.sand-08.nym2')
        mock_get_running_jobs.assert_called_with(data_source=None, host_ran_on='05.agg.sand-08.nym2', record_count=50, filter_string='', statuses=[], hour=None)

if __name__ == '__main__':
    import unittest
    unittest.main()
