"""Tests for the job detail endpoint"""
import datetime
from xml.etree import ElementTree

import unittest
from mock import Mock, patch
from endpoints.job_detail import JobDetailEndpoint
from test.test_base import EndpointTest
from endpoints import app
from endpoints.database import (db, DMFBase, Job, JobSchedule, JobScheduleRule,
                                JobConflict, RunningJob, DpaasGroups)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class JobDetailEndpointTest(EndpointTest):

    def setUp(self):
        super(JobDetailEndpointTest, self).setUp()
        self.db = db

        # patch these to prevent any I/O
        self.get_alert_services_patcher = patch('utils.maestro_client.get_alert_services')
        self.mock_get_alert_services = self.get_alert_services_patcher.start()
        self.mock_get_alert_services.return_value = ['poo']

        DMFBase.metadata.create_all(db.engine)

        try:
            job_entry = Job(
                name='dan_dan',
                job_type='agg',
                config_file='han_dynasty.inc',
                table_name='dan_dan',
                lastupd=datetime.datetime.utcfromtimestamp(555638400),
                is_monitored=0,
                time_interval='day',
                is_system=0,
                description='',
                owner_group_id=1)

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
                alert_svcs='poo',
                paused_until=datetime.datetime.utcfromtimestamp(0),
                first_eligible_hour=datetime.datetime.utcfromtimestamp(10),
                resource_queue='p2')

            job_schedule_rule_entry = JobScheduleRule(
                id=1,
                job_schedule_id=271828,
                table_name='noodles',
                load_threshold=None,
                hour_offset=None,
                lastupd=datetime.datetime.utcfromtimestamp(555638400),
                require_closed_hour=1,
                data_source='east_village')

            job_conflict_entry = JobConflict(
                job_name='dan_dan',
                conflicting_job_name='hunger',
                data_source='east_village',
                conflicting_data_source='east_village',
                lastupd=datetime.datetime.utcfromtimestamp(555638400),
                id=1)

            dependent_job_schedule_entry = JobSchedule(
                id=1000000,
                job_name='scratch_off_lottery_ticket',
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
                alert_svcs='poo',
                paused_until=datetime.datetime.utcfromtimestamp(0),
                first_eligible_hour=datetime.datetime.utcfromtimestamp(10))

            dependent_job_schedule_rule_entry = JobScheduleRule(
                id=2,
                job_schedule_id=1000000,
                table_name='dan_dan',
                load_threshold=None,
                hour_offset=None,
                lastupd=datetime.datetime.utcfromtimestamp(555638400),
                require_closed_hour=1,
                data_source='east_village')

            job_schedule_entry_no_host = JobSchedule(
                id=271829,
                job_name='dan_dan',
                description='',
                min_time_passed=70,
                priority=42,
                active=1,
                bypass_validation=0,
                min_minutes_between_runs=None,
                lastupd=datetime.datetime.utcfromtimestamp(555638400),
                close_hour=1,
                env_to_run_in='sand/nym2',
                data_source='east_village',
                reprocess=1,
                alert_svcs='poo',
                paused_until=datetime.datetime.utcfromtimestamp(0),
                first_eligible_hour=datetime.datetime.utcfromtimestamp(10),
                resource_queue='p2')

            dpaas_groups_entry = DpaasGroups(
                id=1,
                group_name='dpaas_poop_team',
                lastupd=datetime.datetime.utcfromtimestamp(555638400))

            db.session.add(job_entry)
            db.session.add(job_schedule_entry)
            db.session.add(job_schedule_rule_entry)
            db.session.add(job_conflict_entry)
            db.session.add(dependent_job_schedule_entry)
            db.session.add(dependent_job_schedule_rule_entry)
            db.session.add(job_schedule_entry_no_host)
            db.session.add(dpaas_groups_entry)
            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()

    def tearDown(self):
        self.get_alert_services_patcher.stop()
        DMFBase.metadata.drop_all(db.engine)

    def test_returns_correct_data(self):
        response = self.app.get('/job_detail?job_id=271828')
        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        assert html.find('.//*[@class="job_name"]').text == 'dan_dan'
        assert html.find('.//*[@class="job_schedule_data_source"]').text == 'east_village'
        assert html.find('.//*[@class="job_schedule_rule_table_name"]').text == 'noodles'
        assert html.find('.//*[@class="job_conflict_conflicting_job_name"]').text == 'hunger'
        assert html.find('.//*[@class="job_schedule_first_eligible_hour"]').text == '1970-01-01 00:00:10'
        assert html.find('.//*[@class="depended_on_job_name"]').text == 'scratch_off_lottery_ticket'
        assert html.find('.//*[@class="job_schedule_resource_queue"]').text == 'p2'

    def test_detects_null_dependency_data_source(self):
        """XXX- A job can depend on another job if both jobs have the same data source and
        the job_schedule_rule entry has a null data source"""
        try:
            db.session.query(JobScheduleRule).filter(id == 2).\
                update({"data_source":None})
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()

        response = self.app.get('/job_detail?job_id=271828')
        html = ElementTree.fromstring(response.data)
        assert html.find('.//*[@class="depended_on_job_name"]').text == 'scratch_off_lottery_ticket'

    @patch('endpoints.job_detail.get_running_jobs')
    def test_computes_stats_correctly(self, mock_get_running_jobs):
        running_job_1 = RunningJob(
            job_id=271828,
            status='completed',
            started_on=datetime.datetime(2000, 1, 1, 10, 15, 0),
            completed_on=datetime.datetime(2000, 1, 1, 10, 15, 30))

        running_job_2 = RunningJob(
            job_id=271828,
            status='completed',
            started_on=datetime.datetime(2000, 2, 1, 9, 0, 0),
            completed_on=datetime.datetime(2000, 2, 1, 9, 0, 45))

        running_job_3 = RunningJob(
            job_id=271828,
            status='failed',
            started_on=datetime.datetime(2000, 3, 1, 5, 20, 10),
            completed_on=datetime.datetime(2000, 3, 1, 5, 20, 50))

        running_job_4 = RunningJob(
            job_id=271828,
            status='failed',
            started_on=datetime.datetime(2000, 4, 1, 7, 45, 5),
            completed_on=datetime.datetime(2000, 4, 1, 7, 45, 25))

        mock_get_running_jobs.return_value = [running_job_1, running_job_2, running_job_3, running_job_4]
        response = self.app.get('/job_detail?job_id=271828')
        mock_get_running_jobs.assert_called_once_with(job_id=271828, record_count=500)

        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        stats = html.find('.//*[@id="completed_runs_stats"]')
        assert stats.find('.//*[@id="jobs_completed"]').text == '2'
        assert stats.find('.//*[@id="completed_median"]').text == '0:00:38'
        assert stats.find('.//*[@id="completed_avg"]').text == '0:00:38'
        assert stats.find('.//*[@id="completed_95_percentile"]').text == '0:00:45'
        assert stats.find('.//*[@id="completed_99_percentile"]').text == '0:00:45'
        stats = html.find('.//*[@id="failed_runs_stats"]')
        assert stats.find('.//*[@id="jobs_failed"]').text == '2'
        assert stats.find('.//*[@id="failed_median"]').text == '0:00:30'
        assert stats.find('.//*[@id="failed_avg"]').text == '0:00:30'
        assert stats.find('.//*[@id="failed_95_percentile"]').text == '0:00:40'
        assert stats.find('.//*[@id="failed_99_percentile"]').text == '0:00:40'

if __name__ == '__main__':
    import unittest
    unittest.main()
