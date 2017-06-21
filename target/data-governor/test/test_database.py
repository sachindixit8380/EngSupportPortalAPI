import datetime

from test.test_base import EndpointTest
from endpoints.database import (db, DMFBase, RunningJob, State, get_running_jobs,
                                upsert_state, JobConflict, get_job_conflicts)
from endpoints import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class DatabaseEndpointTest(EndpointTest):

    def setUp(self):
        super(DatabaseEndpointTest, self).setUp()
        self.db = db
        DMFBase.metadata.create_all(db.engine)
        try:
            pending_entry = RunningJob(
                id=1,
                job_id=2,
                data_source='islay',
                hour=datetime.datetime(2014, 05, 04, 00),
                name='lagavulin',
                table_name='lagavulin',
                config_file='/mnt/glass',
                job_type='agg',
                status='pending',
                request=None,
                response=None,
                job='drink_scotch',
                information=None,
                created_on=datetime.datetime.utcfromtimestamp(1399507200),
                started_on=datetime.datetime.utcfromtimestamp(1399507200),
                completed_on = datetime.datetime.utcfromtimestamp(1399510923),
                reprocess=0)

            failed_entry = RunningJob(
                id=2,
                job_id=3,
                data_source='hadoop_quest',
                hour=datetime.datetime(2014, 05, 04, 00),
                name='parental_expectations',
                table_name='medical_school',
                config_file='/dev/null',
                job_type='agg',
                status='failed',
                request=None,
                response=None,
                job='doctor',
                information=None,
                created_on=datetime.datetime.utcfromtimestamp(1399507200),
                started_on=datetime.datetime.utcfromtimestamp(1399507200),
                completed_on = datetime.datetime.utcfromtimestamp(1),
                reprocess=0)

            completed_entry = RunningJob(
                id=3,
                job_id=4,
                data_source='hadoop_cypress',
                hour=datetime.datetime(2014, 05, 05, 01),
                name='jawn',
                table_name='jawn_doe',
                config_file='/proc/1',
                job_type='hadoop_job',
                status='completed',
                request=None,
                response=None,
                job='wontshowanyway',
                information=None,
                created_on=datetime.datetime.utcfromtimestamp(1399507200),
                started_on=datetime.datetime.utcfromtimestamp(1399507200),
                completed_on = datetime.datetime.utcfromtimestamp(1399510923),
                reprocess=0)

            db.session.add(pending_entry)
            db.session.add(failed_entry)
            db.session.add(completed_entry)

            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()


    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)

    def test_get_running_jobs_returns_correct_record_count(self):
        """Test to make sure the get_running_jobs function returns
        the appropriate number of entries"""
        response = get_running_jobs(record_count=2)
        assert len(response) == 2

    def test_data_source_filter(self):
        response = get_running_jobs(data_source='islay')
        assert len(response) == 1
        assert response[0].name == 'lagavulin'

    def test_status_filter(self):
        response = get_running_jobs(statuses=['failed'])
        assert len(response) == 1
        assert response[0].name == 'parental_expectations'

    def test_filter(self):
        response = get_running_jobs(filter_string='rental_expect')
        assert len(response) == 1
        assert response[0].name == 'parental_expectations'

    def test_job_id_filter(self):
        response = get_running_jobs(job_id=4)
        assert len(response) == 1
        assert response[0].name == 'jawn'

    def test_hour_filter(self):
        response = get_running_jobs(hour='2014-05-05 01:00:00')
        assert len(response) == 1
        assert response[0].name == 'jawn'

    def test_prefix_hour_filter(self):
        response = get_running_jobs(hour='2014-05-05')
        assert len(response) == 1
        assert response[0].name == 'jawn'

    def test_table_name_filter(self):
        response = get_running_jobs(table_name='lagavulin')
        assert len(response) == 1
        assert response[0].id == 1

    def test_upsert_inserts_new_row(self):
        log_message = upsert_state(hour=datetime.datetime(2014, 7, 16, 13),
                                   table_name='singapore_cable_break',
                                   data_source='hadoop_quest')
        state_entry = db.session.query(State).filter(
                          State.hour==datetime.datetime(2014, 7, 16, 13),
                          State.table_name=='singapore_cable_break').all()

        assert state_entry[0].data_source == 'hadoop_quest'
        assert state_entry[0].hour_closed == 0
        assert "Created a new state entry for 2014-07-16 13:00:00-singapore_cable_break-hadoop_quest- with hour_closed 0" in log_message

    def test_upsert_updates_existing_row(self):
        new_state_entry = State(hour=datetime.datetime(2014, 7, 16, 13),
                            table_name='singapore_cable_break',
                            data_source='hadoop_quest',
                            version='',
                            hour_closed=0,
                            last_run=datetime.datetime.now())
        db.session.add(new_state_entry)
        db.session.commit()

        log_message = upsert_state(hour=datetime.datetime(2014, 7, 16, 13),
                                   table_name='singapore_cable_break',
                                   data_source='hadoop_quest',
                                   hour_closed=1)

        state_entry = db.session.query(State).filter(
                          State.hour==datetime.datetime(2014, 7, 16, 13),
                          State.table_name=='singapore_cable_break').all()

        assert len(state_entry) == 1
        assert state_entry[0].hour_closed == 1
        assert "Updated the state entry for 2014-07-16 13:00:00-singapore_cable_break-hadoop_quest- to hour_closed 1" in log_message

    def test_get_job_conflicts_with_job_name(self):
        job_conflict_entry = JobConflict(job_name='oil',
                                         data_source='deepwater_horizon',
                                         conflicting_job_name='water',
                                         conflicting_data_source='the_gulf')
        db.session.add(job_conflict_entry)
        db.session.commit()

        conflicts = get_job_conflicts('oil', 'deepwater_horizon')
        assert len(conflicts) == 1
        assert conflicts[0].job_name == 'oil'
        assert conflicts[0].data_source == 'deepwater_horizon'
        assert conflicts[0].conflicting_job_name == 'water'
        assert conflicts[0].conflicting_data_source == 'the_gulf'

    def test_get_job_conflicts_with_conflicting_job_name(self):
        job_conflict_entry = JobConflict(job_name='oil',
                                         data_source='deepwater_horizon',
                                         conflicting_job_name='water',
                                         conflicting_data_source='the_gulf')
        db.session.add(job_conflict_entry)
        db.session.commit()

        conflicts = get_job_conflicts('water', 'the_gulf')
        assert len(conflicts) == 1
        assert conflicts[0].job_name == 'oil'
        assert conflicts[0].data_source == 'deepwater_horizon'
        assert conflicts[0].conflicting_job_name == 'water'
        assert conflicts[0].conflicting_data_source == 'the_gulf'

    def test_get_job_conflicts_with_null_data_source(self):
        job_conflict_entry = JobConflict(job_name='oil',
                                         data_source=None,
                                         conflicting_job_name='water',
                                         conflicting_data_source='the_gulf')
        db.session.add(job_conflict_entry)
        db.session.commit()

        conflicts = get_job_conflicts('oil', 'deepwater_horizon')
        assert len(conflicts) == 1
        assert conflicts[0].job_name == 'oil'
        assert conflicts[0].data_source == None
        assert conflicts[0].conflicting_job_name == 'water'
        assert conflicts[0].conflicting_data_source == 'the_gulf'

    def test_get_job_conflicts_with_null_conflicting_data_source(self):
        job_conflict_entry = JobConflict(job_name='oil',
                                         data_source='deepwater_horizon',
                                         conflicting_job_name='water',
                                         conflicting_data_source=None)
        db.session.add(job_conflict_entry)
        db.session.commit()

        conflicts = get_job_conflicts('water', 'the_gulf')
        assert len(conflicts) == 1
        assert conflicts[0].job_name == 'oil'
        assert conflicts[0].data_source == 'deepwater_horizon'
        assert conflicts[0].conflicting_job_name == 'water'
        assert conflicts[0].conflicting_data_source == None

if __name__ == '__main__':
    import unittest
    unittest.main()
