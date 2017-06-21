"""Tests for the bad_records endpoint"""

import datetime
from xml.etree import ElementTree

import unittest
from endpoints.late_data import HTMLLateDataEndpoint
from endpoints import app
from test.test_base import EndpointTest

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

from endpoints.database import (db, DMFBase, DataSources, Job, JobSchedule, JobScheduleRule, State, LoadLog)

class BadRecordsEndpointTests(EndpointTest):
    """Tests of the /bad_records endpoint."""

    def setUp(self):
        super(BadRecordsEndpointTests, self).setUp()
        self.db = db
        DMFBase.metadata.create_all(db.engine)
        self.flask_app = app
        session = db.session()

        session.add(DataSources(name='hadoop_cypress', datacenter='lax1'))
        session.add(Job(name='test_job', table_name='test_job'))
        session.commit()

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)
        super(BadRecordsEndpointTests, self).tearDown()

    def test_post_error_status_code(self):
        """Do we return a 405 for an unsupported HTTP method?"""
        response = self.app.post('/bad_records')
        assert response.status_code == 405

    def test_get_bad_records_is_html(self):
        """Is the view_status endpoint is properly returning HTML?"""
        response = self.app.get('/bad_records')
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']

    def test_bad_records(self):
        """Do we get correct data in the response when there's a bad records?"""
        session = db.session()
        target_hour = '2016-04-18 17:00:00' 
        job_name = 'test_job'

        late_load_log_entry = LoadLog(
            table_name=job_name,
            hour=target_hour,
            size_mb=100,
            last_run=datetime.datetime.now(),
            data_source='hadoop_cypress',
            good_records=100,
            bad_records=5,
            hostname='hostless')

        session.add(load_log_entry)
        session.commit()

        rv = self.app.get('/view_late_data')
        html = ElementTree.fromstring(rv.data)
        runs_with_late_data = html.findall('.//*[@class="run_with_late_data"]')
        assert len(runs_with_late_data) == 1
        assert 'test_job' == runs_with_late_data[0].find('.//*[@class="job_name"]').text
        assert runs_with_late_data[0].find('.//*[@name="late_data_values"]') is not None
        assert runs_with_late_data[0].find('.//*[@value="{0}"]'.format(correct_value)) is not None

if __name__ == '__main__':
    import unittest
    unittest.main()
