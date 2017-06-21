"""Tests for the view_late_data endpoint"""

import datetime
from xml.etree import ElementTree

import unittest
from endpoints.late_data import HTMLLateDataEndpoint
from endpoints import app
from test.test_base import EndpointTest

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

from endpoints.database import (db, DMFBase, DataSources, Job, JobSchedule, JobScheduleRule, State, LoadLog)

class LateDataEndpointTests(EndpointTest):
    """Tests of the /view_late_data endpoint."""

    def setUp(self):
        super(LateDataEndpointTests, self).setUp()
        self.db = db
        DMFBase.metadata.create_all(db.engine)
        self.flask_app = app
        session = db.session()

        session.add(DataSources(name='hadoop_quest', datacenter='nym2'))
        session.add(Job(name='test_job', table_name='test_job'))
        session.commit()

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)
        super(LateDataEndpointTests, self).tearDown()

    def test_post_error_status_code(self):
        """Do we return a 405 for an unsupported HTTP method?"""
        response = self.app.post('/view_late_data')
        assert response.status_code == 405

    def test_get_view_late_data_is_html(self):
        """Is the view_status endpoint is properly returning HTML?"""
        response = self.app.get('/view_late_data')
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']

    def test_late_log(self):
        """Do we get correct data in the response when there's a late log?"""
        session = db.session()
        target_hour = datetime.datetime.now() - datetime.timedelta(hours=3)
        target_hour = target_hour.replace(minute=0, second=0, microsecond=0)

        session.add(JobSchedule(
            id=1,
            job_name='test_job',
            active=1,
            close_hour=1,
            data_source='hadoop_quest',
            reprocess=1,
            min_time_passed=60
        ))

        session.add(JobScheduleRule(
            job_schedule_id=1,
            table_name='test_log',
            data_source='hadoop_quest'
        ))

        job_state_entry = State(
            hour=target_hour,
            table_name='test_job',
            purged=0,
            last_run=datetime.datetime.now() - datetime.timedelta(minutes=3),
            data_source='hadoop_quest',
            dependency=1, # it is expected dependency is set = 1 on arrival of late data
            reprocess=0)

        log_state_entry = State(
            hour=target_hour,
            table_name='test_log',
            purged=0,
            last_run=datetime.datetime.now(),
            data_source='hadoop_quest',
            dependency=0,
            reprocess=0)

        load_log_entry = LoadLog(
            table_name='test_log',
            hour=target_hour,
            size_mb=100,
            last_run=datetime.datetime.now() - datetime.timedelta(minutes=4),
            data_source='hadoop_quest',
            hostname='hostess')

        late_load_log_entry = LoadLog(
            table_name='test_log',
            hour=target_hour,
            size_mb=0,
            last_run=datetime.datetime.now(),
            data_source='hadoop_quest',
            hostname='hostess')

        session.add(job_state_entry)
        session.add(log_state_entry)
        session.add(load_log_entry)
        session.add(late_load_log_entry)
        session.commit()

        correct_value = str(target_hour) + '^' + 'hadoop_quest' + '^' + 'test_log'
        rv = self.app.get('/view_late_data')
        html = ElementTree.fromstring(rv.data)
        runs_with_late_data = html.findall('.//*[@class="run_with_late_data"]')
        assert len(runs_with_late_data) == 1
        assert 'test_job' == runs_with_late_data[0].find('.//*[@class="job_name"]').text
        assert runs_with_late_data[0].find('.//*[@name="late_data_values"]') is not None
        assert runs_with_late_data[0].find('.//*[@value="{0}"]'.format(correct_value)) is not None

    def test_late_data_for_purged_job(self):
        """Do we get correct data in the response when a dependent state entry is late but purged?"""
        session = db.session()
        target_hour = datetime.datetime.now() - datetime.timedelta(hours=3)
        target_hour = target_hour.replace(minute=0, second=0, microsecond=0)

        session.add(JobSchedule(
            id=1,
            job_name='test_job',
            active=1,
            close_hour=1,
            data_source='hadoop_quest',
            reprocess=1,
            min_time_passed=60
        ))

        session.add(JobScheduleRule(
            job_schedule_id=1,
            table_name='test_log',
            data_source='hadoop_quest'
        ))

        job_state_entry = State(
            hour=target_hour,
            table_name='test_job',
            purged=0,
            last_run=datetime.datetime.now() - datetime.timedelta(minutes=3),
            data_source='hadoop_quest',
            dependency=1, # it is expected dependency is set = 1 on arrival of late data
            reprocess=0)

        log_state_entry = State(
            hour=target_hour,
            table_name='test_log',
            purged=1,
            last_run=datetime.datetime.now(),
            data_source='hadoop_quest',
            dependency=0,
            reprocess=0)

        late_load_log_entry = LoadLog(
            table_name='test_log',
            hour=target_hour,
            size_mb=0,
            last_run=datetime.datetime.now(),
            data_source='hadoop_quest',
            hostname='hostess')

        session.add(job_state_entry)
        session.add(log_state_entry)
        session.add(late_load_log_entry)
        session.commit()

        rv = self.app.get('/view_late_data')
        html = ElementTree.fromstring(rv.data)
        runs_with_late_data = html.findall('.//*[@class="run_with_late_data"]')
        assert runs_with_late_data == []

    def test_no_entry_for_hour_before_first_eligible_hour(self):
        session = db.session()
        target_hour = datetime.datetime.now() - datetime.timedelta(hours=3)
        target_hour = target_hour.replace(minute=0, second=0, microsecond=0)

        session.add(JobSchedule(
            id=1,
            job_name='test_job',
            active=1,
            close_hour=1,
            data_source='hadoop_quest',
            reprocess=1,
            min_time_passed=60,
            first_eligible_hour = target_hour + datetime.timedelta(hours=3)
        ))

        session.add(JobScheduleRule(
            job_schedule_id=1,
            table_name='test_log',
            data_source='hadoop_quest'
        ))

        job_state_entry = State(
            hour=target_hour,
            table_name='test_job',
            purged=0,
            last_run=datetime.datetime.now() - datetime.timedelta(minutes=3),
            data_source='hadoop_quest',
            dependency=1, # it is expected dependency is set = 1 on arrival of late data
            reprocess=0)

        log_state_entry = State(
            hour=target_hour,
            table_name='test_log',
            purged=0,
            last_run=datetime.datetime.now(),
            data_source='hadoop_quest',
            dependency=0,
            reprocess=0)

        late_load_log_entry = LoadLog(
            table_name='test_log',
            hour=target_hour,
            size_mb=0,
            last_run=datetime.datetime.now(),
            data_source='hadoop_quest',
            hostname='hostess')

        session.add(job_state_entry)
        session.add(log_state_entry)
        session.add(late_load_log_entry)
        session.commit()

        rv = self.app.get('/view_late_data')
        html = ElementTree.fromstring(rv.data)
        runs_with_late_data = html.findall('.//*[@class="run_with_late_data"]')
        assert runs_with_late_data == []

if __name__ == '__main__':
    import unittest
    unittest.main()
