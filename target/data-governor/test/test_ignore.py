import datetime
import unittest
from endpoints.ignore_late_data import IgnoreLateData
from endpoints import app
from test.test_base import EndpointTest

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

from endpoints.database import db, DMFBase, State

import pprint

class IgnoreLateDataTests(EndpointTest):
    """Tests of the /ignore endpoint"""

    def setUp(self):
        super(IgnoreLateDataTests, self).setUp()
        self.test_data = {"job_name": "test_ignore_job", "job_table_name": "test_ignore_job", "test_log": "test_ignore_ooga_log", "data_source": "hadoop_quest"}
        self.db = db
        DMFBase.metadata.create_all(db.engine)
        self.flask_app = app

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)
        super(IgnoreLateDataTests, self).tearDown()

    def test_get_error_status_code(self):
        response = self.app.get('/ignore')
        assert response.status_code == 405

    def test_not_log_ignore(self):
        late_data_values = ' ' + '^' + self.test_data['data_source'] + '^' + 'LOL'
        ignore_data = { 'late_data_values': late_data_values }
        response = self.app.post('/ignore', data=ignore_data)
        assert response.status_code == 400

    def test_missing_params(self):
        late_data_values = 'test_log' + '^' + self.test_data['data_source']
        ignore_data = {'late_data_values': late_data_values}
        response = self.app.post('/ignore', data=ignore_data)
        assert response.status_code == 400

    def test_ignore_late_data_ignores_correct_hour(self):
        session = db.session()
        target_hour = datetime.datetime.now() - datetime.timedelta(hours=1)
        target_hour = target_hour.replace(minute=0, second=0, microsecond=0)
        try:
            job_state = State(
                hour=target_hour,
                table_name=self.test_data['job_table_name'],
                version='',
                job_id=1,
                purged=0,
                validated=0,
                last_run=datetime.datetime.now() - datetime.timedelta(minutes=3),
                hour_closed=1,
                data_source=self.test_data['data_source'],
                dependency=0,
                origin=None,
                reprocess=0)

            log_state = State(
                hour=target_hour,
                table_name=self.test_data['test_log'],
                version='',
                job_id=2,
                purged=0,
                validated=0,
                last_run=datetime.datetime.now(),
                hour_closed=1,
                data_source=self.test_data['data_source'],
                dependency=0,
                origin=None,
                reprocess=0)

            session.add(job_state)
            session.add(log_state)
            session.commit()
        except Exception, e:
            print e
            session.rollback()
            self.tearDown()

        late_data_values = str(target_hour) + '^' + self.test_data['data_source'] + '^' + self.test_data['test_log']
        ignore_data = { 'late_data_values': late_data_values }
        response = self.app.post('/ignore', data=ignore_data)

        state_entry = db.session.query(State).filter(\
                State.hour==target_hour,\
                State.table_name==self.test_data['test_log'],\
                State.data_source==self.test_data['data_source']
            ).first()

        new_last_run = target_hour.replace(minute=0, second=0) + datetime.timedelta(hours=1)
        assert state_entry.last_run.strftime('%Y-%m-%d %H:%M:%S') == new_last_run.strftime('%Y-%m-%d %H:%M:%S')
        assert response.status_code == 302

    def test_ignore_late_data_ignores_multiple_correct_hours(self):
        session = db.session()
        target_hour = datetime.datetime.now() - datetime.timedelta(hours=3)
        target_hour = target_hour.replace(minute=0, second=0, microsecond=0)
        target_hour_2 = datetime.datetime.now() - datetime.timedelta(hours=2)
        target_hour_2 = target_hour.replace(minute=0, second=0, microsecond=0)
        try:
            job_state_1 = State(
                hour=target_hour,
                table_name=self.test_data['job_table_name'],
                version='',
                job_id=1,
                purged=0,
                validated=0,
                last_run=datetime.datetime.now() - datetime.timedelta(minutes=3),
                hour_closed=1,
                data_source=self.test_data['data_source'],
                dependency=0,
                origin=None,
                reprocess=0)

            log_state_1 = State(
                hour=target_hour,
                table_name=self.test_data['test_log'],
                version='',
                job_id=2,
                purged=0,
                validated=0,
                last_run=datetime.datetime.now(),
                hour_closed=1,
                data_source=self.test_data['data_source'],
                dependency=0,
                origin=None,
                reprocess=0)

            job_state_2 = State(
                hour=target_hour_2,
                table_name=self.test_data['job_table_name']+'_2',
                version='steve',
                job_id=1,
                purged=0,
                validated=0,
                last_run=datetime.datetime.now() - datetime.timedelta(minutes=3),
                hour_closed=1,
                data_source='tupac',
                dependency=0,
                origin=None,
                reprocess=0)

            log_state_2 = State(
                hour=target_hour_2,
                table_name=self.test_data['test_log']+'_2',
                version='steve',
                job_id=2,
                purged=0,
                validated=0,
                last_run=datetime.datetime.now(),
                hour_closed=1,
                data_source='tupac',
                dependency=0,
                origin=None,
                reprocess=0)



            session.add(job_state_1)
            session.add(job_state_2)
            session.add(log_state_1)
            session.add(log_state_2)
            session.commit()
        except Exception, e:
            print e
            session.rollback()
            self.tearDown()

        ignore_data = {'late_data_values': [str(target_hour) + '^' + self.test_data['data_source'] + '^' + self.test_data['test_log'], str(target_hour_2) + '^' + 'tupac' + '^' + self.test_data['test_log']+'_2']}
        response = self.app.post('/ignore', data=ignore_data)

        state_entry = db.session.query(State).filter(\
                State.hour==target_hour,\
                State.table_name==self.test_data['test_log'],\
                State.data_source==self.test_data['data_source']
            ).first()

        new_last_run = target_hour.replace(minute=0, second=0) + datetime.timedelta(hours=1)
        assert state_entry.last_run.strftime('%Y-%m-%d %H:%M:%S') == new_last_run.strftime('%Y-%m-%d %H:%M:%S')

        state_entry_2 = db.session.query(State).filter(\
                State.hour==target_hour_2,\
                State.table_name==self.test_data['test_log'],\
                State.data_source==self.test_data['data_source']
            ).first()

        new_last_run = target_hour_2.replace(minute=0, second=0) + datetime.timedelta(hours=1)
        assert state_entry.last_run.strftime('%Y-%m-%d %H:%M:%S') == new_last_run.strftime('%Y-%m-%d %H:%M:%S')

        assert response.status_code == 302


if __name__ == '__main__':
    import unittest
    unittest.main()
