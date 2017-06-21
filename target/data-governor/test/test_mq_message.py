"""Tests for the "/mq_message" endpoint"""

import datetime
from mock import patch

from test.test_base import EndpointTest
from endpoints.database import db, DMFBase, JobMQMessage
from endpoints.mq_message import MQMessageEndpoint

class MQMessageEndpointTests(EndpointTest):
    """Tests for the '/mq_message' endpoint."""

    def setUp(self):
        super(MQMessageEndpointTests, self).setUp()

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        session = db.session()

        try:
            mq_entry = JobMQMessage(
                id=1,
                job_schedule_id=1337,
                message='greetings earthling',
                active=0,
                lastupd=datetime.datetime(2015, 1, 1, 10, 11, 12))

            mq_entry_1 = JobMQMessage(
                id=3,
                job_schedule_id=9999,
                message='greetings alien',
                active=1,
                lastupd=datetime.datetime(2015, 1, 2, 11, 12, 13))

            session.add(mq_entry)
            session.add(mq_entry_1)
            session.commit()
        except Exception, e:
            print e
            session.rollback()
            self.tearDown()

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)
        super(MQMessageEndpointTests, self).tearDown()

    def test_post_error_status_code(self):
        """Is the status code 400 if we post without any data?"""
        response = self.app.post('/mq_message', data={})
        assert response.status_code == 400

    @patch('endpoints.mq_message.url_for')
    def test_valid_toggle_active(self, mock_url_for):
        mq_entry = self.db.session.query(JobMQMessage).filter(
                JobMQMessage.id==1).first()
        assert mq_entry.active == False;

        test_data = {"id":1,
                     "active":1,
                     "job_schedule_id":1337}
        response = self.app.post('/mq_message', data=test_data)
        mock_url_for.assert_called_with('job_detail', job_id='1337', _anchor='job_mq_message')
        assert response.status_code == 302

        updated_mq_entry = self.db.session.query(JobMQMessage).filter(
                JobMQMessage.id==test_data['id']).first()
        assert updated_mq_entry.active == True

    def test_string_active(self):
        test_data = {"id":3,
                     "active":"string",
                     "job_schedule_id":123}
        response = self.app.post('/mq_message', data=test_data)
        assert response.status_code == 400
        assert "Non-integer value for active" in response.data

    def test_invalid_active(self):
        test_data = {"id":3,
                     "active":3,
                     "job_schedule_id":123}
        response = self.app.post('/mq_message', data=test_data)
        assert response.status_code == 400
        assert "The only acceptable values for active are 1 and 0" in response.data

    def test_missing_active(self):
        test_data = {"id":3,
                     "job_schedule_id":123}
        response = self.app.post('/mq_message', data=test_data)
        assert response.status_code == 400
        assert "Insufficient information to update job_mq_message" in response.data

    def test_missing_id(self):
        test_data = {"active":1,
                     "job_schedule_id":123}
        response = self.app.post('/mq_message', data=test_data)
        assert response.status_code == 400
        assert "Insufficient information to update job_mq_message" in response.data

if __name__ == '__main__':
    import unittest
    unittest.main()
