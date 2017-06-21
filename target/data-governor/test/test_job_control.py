"""Tests for the job_activate endpoint"""

import unittest
import datetime
from endpoints.job_control import JobControl
from endpoints import app
from endpoints.database import db, DMFBase, JobSchedule
from test.test_base import EndpointTest

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True


class JobControlTest(EndpointTest):

    def setUp(self):
        super(JobControlTest, self).setUp()

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        self.flask_app = app
        session = db.session()
        try:
            job_schedule = JobSchedule(
                id=1,
                job_name="foo",
                description="I'm just chillin",
                min_time_passed=0,
                priority=100,
                active=1,
                bypass_validation=0,
                min_minutes_between_runs=None,
                lastupd=datetime.datetime.now(),
                close_hour=1,
                host_to_run_on='steve.megacorp.net/enterprise/',
                data_source='ghostface_killah',
                reprocess=1,
                paused_until=datetime.datetime.now())

            session.add(job_schedule)
            session.commit()
        except Exception, e:
            print e
            session.rollback()
            self.tearDown()

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)
        super(JobControlTest, self).tearDown()

    def test_get_method(self):
        response = self.app.get('/job_control')
        assert response.status_code == 200

if __name__ == '__main__':
    import unittest
    unittest.main()
