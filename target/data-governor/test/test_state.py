"""Tests for the "/state" endpoint"""

import copy, json
from datetime import datetime
from mock import patch

from xml.etree import ElementTree

from test.test_base import EndpointTest
from endpoints.state import StateEndpoint
from endpoints.database import db, DMFBase, State, DataSources
from endpoints import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

test_data = {"hour":"2013-09-30 04:00:00",
             "table_name":"test_table",
             "data_source":"hadoop_cypress",
             "version":"",
             "purged":0,
             "hour_closed":1,
             "dependency":0}

class StateEndpointTests(EndpointTest):
    """Tests of the '/state' endpoint."""
    test_data = test_data

    def setUp(self):
        super(StateEndpointTests, self).setUp()

        self.get_data_sources_patcher = patch('utils.validation_funcs.get_data_sources')
        self.mock_get_data_sources = self.get_data_sources_patcher.start()
        self.mock_get_data_sources.return_value = ['hadoop_cypress', 'hadoop_quest', 'tupac']

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        self.flask_app = app

        try:
            data_source = DataSources(
                name='hadoop_cypress',
                datacenter='lax1',
                scheduling_host='foo',
                type='foo',
                )

            session = db.session()
            session.add(data_source)

            state = State(
                hour=datetime.strptime(test_data['hour'], '%Y-%m-%d %H:%M:%S'),
                table_name=test_data['table_name'],
                version=test_data['version'],
                job_id=530,
                data_source=test_data['data_source'],
                reprocess=False,
                purged=False,
                validated=False,
                hour_closed=test_data['hour_closed'],
                dependency=False,
                )

            state_entry = State(
                hour=datetime(2014, 7, 4, 0, 0, 0),
                table_name='el_table',
                version='v9.11',
                job_id=987,
                purged=0,
                validated=1,
                last_run=datetime(2014, 7, 16, 0, 0, 0),
                hour_closed=1,
                sync_time=datetime.now(),
                data_source='tupac',
                dependency=0,
                origin='feed_me',
                reprocess=0)

            session.add(state)
            session.add(state_entry)
            session.commit()
        except Exception, e:
            print e
            session.rollback()
            self.tearDown()

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)
        super(StateEndpointTests, self).tearDown()

    def test_get_method(self):
        response = self.app.get('/state')
        assert response.status_code == 200

    def test_get_with_filter(self):
        try:
            state_entry = State(
                hour=datetime(2014, 9, 13, 0, 0, 0),
                table_name='air_hockey_table',
                version='v1.23',
                job_id=1.23,
                purged=0,
                validated=1,
                last_run=datetime(2014, 9, 16, 0, 0, 0),
                hour_closed=1,
                sync_time=datetime.now(),
                data_source='hadoop_quest',
                dependency=0,
                origin='destination',
                reprocess=0)

            db.session.add(state_entry)
            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()

        response = self.app.get('/state?hour_filter=2014-09-13+00%3A00%3A00&data_source=hadoop_quest')
        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        assert html.find('.//span[@class="state_hour"]').text == '2014-09-13 00:00:00'
        assert html.find('.//span[@class="state_table_name"]').text == 'air_hockey_table'
        assert html.find('.//span[@class="state_data_source"]').text == 'hadoop_quest'

    def test_post_error_status_code(self):
        """Is the status code 400 if we post without any data?"""
        response = self.app.post('/state', data={})
        assert response.status_code == 400

    def test_valid_state_update(self):
        """Does state get updated with a proper post call to /state endpoint?"""
        state_entry = self.db.session.query(State).filter(
                          State.hour==datetime.strptime(self.test_data['hour'], '%Y-%m-%d %H:%M:%S'),
                          State.table_name==self.test_data['table_name'],
                          State.data_source==self.test_data['data_source']).first()
        state_entry.hour_closed = False;
        self.db.session.add(state_entry)
        self.db.session.commit()

        before_request = datetime.now()

        response = self.app.post('/state', data=test_data)
        assert response.status_code == 204

        updated_state_entry = self.db.session.query(State).filter(
                                  State.hour==datetime.strptime(self.test_data['hour'], '%Y-%m-%d %H:%M:%S'),
                                  State.table_name==self.test_data['table_name'],
                                  State.data_source==self.test_data['data_source']).first()

        assert updated_state_entry.hour_closed == True
        assert updated_state_entry.last_run > before_request

    def test_valid_state_insert(self):
        """Does state get inserted into with a proper post call to /state endpoint?"""
        test_data_copy = copy.deepcopy(self.test_data)
        test_data_copy['table_name'] = 'test_table_2'

        before_request = datetime.now()

        response = self.app.post('/state', data=test_data_copy)
        assert response.status_code == 204

        updated_state_entry = self.db.session.query(State).filter(
                                  State.hour==datetime.strptime(test_data_copy['hour'], '%Y-%m-%d %H:%M:%S'),
                                  State.table_name==test_data_copy['table_name'],
                                  State.data_source==test_data_copy['data_source']).first()

        assert updated_state_entry.hour_closed == True
        assert updated_state_entry.last_run > before_request

    def test_doesnt_prefix_table_names_with_hadoop_when_disabled(self):
        app.config['STATE_PREFIX_LOG_NAMES_WITH_HADOOP'] = False

        test_data_copy = copy.deepcopy(self.test_data)
        test_data_copy['table_name'] = 'log_experiment'
        test_data_copy['data_source'] = 'hadoop_quest'

        before_request = datetime.now()

        response = self.app.post('/state', data=test_data_copy)
        assert response.status_code == 204

        updated_state_entry = self.db.session.query(State).filter(
                                  State.hour==datetime.strptime(test_data_copy['hour'], '%Y-%m-%d %H:%M:%S'),
                                  State.data_source==test_data_copy['data_source']).first()

        assert updated_state_entry.table_name == 'log_experiment'
        assert updated_state_entry.last_run > before_request

    def test_prefixes_table_names_with_hadoop__when_starts_with_log_and_enabled(self):
        app.config['STATE_PREFIX_LOG_NAMES_WITH_HADOOP'] = True

        test_data_copy = copy.deepcopy(self.test_data)
        test_data_copy['table_name'] = 'log_experiment'
        test_data_copy['data_source'] = 'hadoop_quest'

        before_request = datetime.now()

        response = self.app.post('/state', data=test_data_copy)
        assert response.status_code == 204

        updated_state_entry = self.db.session.query(State).filter(
                                  State.hour==datetime.strptime(test_data_copy['hour'], '%Y-%m-%d %H:%M:%S'),
                                  State.data_source==test_data_copy['data_source']).first()

        assert updated_state_entry.table_name == 'hadoop_log_experiment'
        assert updated_state_entry.last_run > before_request

    def test_bad_hour_closed_field_raises_error(self):
        test_bad_data = {"hour":"2013-09-30 04:00:00",
                         "table_name":"test_table",
                         "data_source":"hadoop_cypress",
                         "hour_closed":"this is not a valid value for hour closed"}

        response = self.app.post('/state', data=test_bad_data)
        assert response.status_code == 400
        assert "Non-integer value for hour_closed" in response.data

    def test_url_params_can_specify_row(self):
        test_data = {"hour_closed": 0}
        response = self.app.post('/state?hour=2013-09-30%2004:00:00&table_name=test_table&data_source=hadoop_cypress', data=test_data)

        updated_state_entry = self.db.session.query(State).filter(
                                  State.hour==datetime.strptime(self.test_data['hour'], '%Y-%m-%d %H:%M:%S'),
                                  State.table_name==self.test_data['table_name'],
                                  State.data_source==self.test_data['data_source']).first()

        assert response.status_code == 204
        assert updated_state_entry.hour_closed == False

    def test_mark_table_as_purged(self):
        test_data = {"purged": 1}
        response = self.app.post('/state?hour=2013-09-30%2004:00:00&table_name=test_table&data_source=hadoop_cypress', data=test_data)

        updated_state_entry = self.db.session.query(State).filter(
                                  State.hour==datetime.strptime(self.test_data['hour'], '%Y-%m-%d %H:%M:%S'),
                                  State.table_name==self.test_data['table_name'],
                                  State.data_source==self.test_data['data_source']).first()

        assert response.status_code == 204
        assert updated_state_entry.purged == 1

    def test_invalid_hour_key(self):
        invalid_data = {"hour":"2014-27-94 86:70:91",
                        "table_name":"el_table",
                        "version":"v9.11",
                        "data_source":"tupac"}
        response = self.app.post('/state', data=invalid_data)
        assert response.status_code == 400
        assert "2014-27-94 86:70:91 is not a valid hour string" in response.data

    def test_edit_purged(self):
        valid_data = {"hour":"2014-07-04 00:00:00",
                      "table_name":"el_table",
                      "version":"v9.11",
                      "data_source":"tupac",
                      "purged":1}
        response = self.app.post('/state', data=valid_data)
        assert response.status_code == 204
        state_entry = db.session.query(State).filter(State.version=='v9.11').first()
        assert state_entry.purged == 1

    def test_edit_hour_closed(self):
        valid_data = {"hour":"2014-07-04 00:00:00",
                      "table_name":"el_table",
                      "version":"v9.11",
                      "data_source":"tupac",
                      "hour_closed":0}
        response = self.app.post('/state', data=valid_data)
        assert response.status_code == 204
        state_entry = db.session.query(State).filter(State.version=='v9.11').first()
        assert state_entry.hour_closed == 0

    def test_edit_last_run(self):
        valid_data = {"hour":"2014-07-04 00:00:00",
                      "table_name":"el_table",
                      "version":"v9.11",
                      "data_source":"tupac",
                      "last_run":"2014-10-06 10:30:59"}
        response = self.app.post('/state', data=valid_data)
        assert response.status_code == 204
        state_entry = db.session.query(State).filter(State.version=='v9.11').first()
        assert state_entry.last_run == datetime(2014,10,6,10,30,59)

    def test_invalid_last_run(self):
        invalid_data = {"hour":"2014-07-04 00:00:00",
                        "table_name":"el_table",
                        "version":"v9.11",
                        "data_source":"tupac",
                        "last_run":"2014-99-83 55:93:87"}
        response = self.app.post('/state', data=invalid_data)
        assert response.status_code == 400
        assert "Unable to parse last_run field" in response.data

    def test_delete_state_entry(self):
        valid_data = {"hour":"2014-07-04 00:00:00",
                      "table_name":"el_table",
                      "version":"v9.11",
                      "data_source":"tupac",
                      "_method":"DELETE"}
        response = self.app.post('/state', data=valid_data)
        assert response.status_code == 204
        state_entry = db.session.query(State).filter(State.version=='v9.11').first()
        assert state_entry == None

    def test_valid_state_creation(self):
        response = self.app.post('/state', data=test_data)
        assert response.status_code == 204
        state_entry = db.session.query(State).filter(State.table_name==test_data['table_name']).first()
        assert state_entry.hour == datetime(2013, 9, 30, 04)
        assert state_entry.table_name == 'test_table'
        assert state_entry.version == ''
        assert state_entry.data_source == 'hadoop_cypress'
        assert state_entry.purged == 0
        assert state_entry.hour_closed == 1
        assert state_entry.dependency == 0

    def test_valid_bulk_state_creation(self):
        valid_data = test_data.copy()
        del valid_data['hour']
        valid_data['start_hour'] = '2014-10-10 10:00:00'
        valid_data['end_hour'] = '2014-10-10 12:00:00'
        valid_data['table_name'] = 'qwerty'

        response = self.app.post('/state', data=valid_data)
        assert response.status_code == 204
        state_entries = db.session.query(State).filter(
                            State.table_name==valid_data['table_name']).all()
        assert len(state_entries) == 3
        for state_entry in state_entries:
            assert state_entry.table_name == 'qwerty'
        assert state_entries[0].hour == datetime(2014, 10, 10, 10)
        assert state_entries[1].hour == datetime(2014, 10, 10, 11)
        assert state_entries[2].hour == datetime(2014, 10, 10, 12)

    def test_hour_and_hour_range(self):
        invalid_data = test_data.copy()
        invalid_data['start_hour'] = '2015-01-01 01:00:00'
        invalid_data['end_hour'] = '2015-01-01 11:00:00'
        response = self.app.post('/state', data=invalid_data)
        assert response.status_code == 400
        assert "Either hour or hour range must be empty" in response.data

    def test_missing_hour_and_hour_range(self):
        invalid_data = test_data.copy()
        del invalid_data['hour']
        response = self.app.post('/state', data=invalid_data)
        assert response.status_code == 400
        assert "Either hour or hour range must be fully provided" in response.data

    def test_start_hour_but_no_end_hour(self):
        invalid_data = test_data.copy()
        del invalid_data['hour']
        invalid_data['start_hour'] = '2015-01-01 01:00:00'
        response = self.app.post('/state', data=invalid_data)
        assert response.status_code == 400
        assert "Either hour or hour range must be fully provided" in response.data

    def test_missing_table_name(self):
        invalid_data = test_data.copy()
        invalid_data['table_name'] = None
        response = self.app.post('/state', data=invalid_data)
        assert response.status_code == 400
        assert "Please specify a table_name" in response.data

    def test_string_value_purged(self):
        invalid_data = test_data.copy()
        invalid_data['purged'] = 'haha_a_string'
        response = self.app.post('/state', data=invalid_data)
        assert response.status_code == 400
        assert "Non-integer value for purged" in response.data

    def test_invalid_integer_hour_closed(self):
        invalid_data = test_data.copy()
        invalid_data['hour_closed'] = 4
        response = self.app.post('/state', data=invalid_data)
        assert response.status_code == 400
        assert "The only acceptable values for hour_closed are 1 and 0" in response.data

    def test_invalid_value_dependency(self):
        invalid_data = test_data.copy()
        invalid_data['dependency'] = 7
        response = self.app.post('/state', data=invalid_data)
        assert response.status_code == 400
        assert "The only acceptable values for dependency are 1 and 0" in response.data

    def test_missing_data_source(self):
        invalid_data = test_data.copy()
        invalid_data['data_source'] = None
        response = self.app.post('/state', data=invalid_data)
        assert response.status_code == 400
        assert "Insufficient information to identify state entry" in response.data

    def test_get_json(self):
        try:
            state_entry = State(
                hour=datetime(2014, 9, 13, 0, 0, 0),
                table_name='agg_budget_backfill_pb',
                version='v000',
                job_id=987,
                purged=0,
                validated=1,
                last_run=datetime(2014, 9, 16, 0, 0, 0),
                hour_closed=1,
                sync_time=datetime(2014, 9, 16, 0, 0, 0),
                data_source='hadoop_quest',
                dependency=0,
                origin='destination',
                reprocess=0)

            db.session.add(state_entry)
            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()

        response_json = json.loads(self.app.get('/state?hour_filter=2014-09-13+00%3A00%3A00&data_source=hadoop_quest',headers={'Accept': 'application/json'}).data)
        expected_json = json.loads('{"state": [{"data_source": "hadoop_quest", "hour": "2014-09-13 00:00:00", "last_run": "2014-09-16 00:00:00","table_name": "agg_budget_backfill_pb"}]}')
        assert (response_json == expected_json)

if __name__ == '__main__':
    import unittest
    unittest.main()
