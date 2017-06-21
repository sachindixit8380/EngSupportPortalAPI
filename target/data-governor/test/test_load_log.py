from datetime import datetime
import pytz
from xml.etree import ElementTree

from test.test_base import EndpointTest
from endpoints.load_log import LoadLogEndpoint
from endpoints.database import db, DMFBase, LoadLog, LogStatus, State
from endpoints import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class LoadLogEndpointTest(EndpointTest):

    def setUp(self):
        super(LoadLogEndpointTest, self).setUp()
        self.db = db
        DMFBase.metadata.create_all(db.engine)

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)

    def test_returns_totals_with_no_data(self):
        resp = self.app.get('/load_log?table_name=unicorn&data_source=dinosaur&hour=1992-09-16+00%3A00%3A00')
        self.assertEquals(200, resp.status_code)
        html = ElementTree.fromstring(resp.data)

        totals = html.findall('.//*[@id="totals"]')
        assert totals[0].find('.//*[@id="totals_good"]').text == '0'
        assert totals[0].find('.//*[@id="totals_bad"]').text == '0'
        assert totals[0].find('.//*[@id="totals_total"]').text == '0'
        assert totals[0].find('.//*[@id="totals_size"]').text == '0'
        assert totals[0].find('.//*[@id="totals_percent"]').text == '0'

    def test_returns_data_for_hour_table_and_data_source(self):
        # stage a whole bunch of data, we'll check for hour 2014-06-20 15, table
        #  name hadoop_log_jawn, data_source hadoop quest
        try:
            # dummy rows we expect to not appear
            db.session.add(LoadLog(
                table_name = 'hadoop_log_jawn',
                hour = datetime(2014, 6, 20, 16, 0, 0, 0, pytz.UTC), # diff hour
                data_source = 'hadoop_quest',
                hostname='hostess',
                last_run = datetime(2014, 6, 20, 16, 11, 0, 0, pytz.UTC))
            )

            db.session.add(LoadLog(
                table_name = 'hadoop_log_not_jawn', # diff table
                hour = datetime(2014, 6, 20, 15, 0, 0, 0, pytz.UTC),
                data_source = 'hadoop_quest',
                hostname='hostess',
                last_run = datetime(2014, 6, 20, 15, 25, 0, 0, pytz.UTC))
            )

            db.session.add(LoadLog(
                table_name = 'hadoop_log_not_jawn',
                hour = datetime(2014, 6, 20, 15, 0, 0, 0, pytz.UTC),
                data_source = 'hadoop_cypress', # diff data source
                hostname='hostess',
                last_run = datetime(2014, 6, 20, 15, 30, 0, 0, pytz.UTC))
            )

            # this row will be kept
            db.session.add(LoadLog(
                table_name = 'hadoop_log_jawn',
                hour = datetime(2014, 6, 20, 15, 0, 0, 0, pytz.UTC),
                version = "v001",
                load_time = 11.0,
                size_mb = 10.0,
                hostname = 'agg.jawn.prod',
                last_run = datetime(2014, 6, 20, 15, 10, 0 , 0, pytz.UTC),
                data_source = 'hadoop_quest',
                good_records = 1,
                bad_records = 2)
            )

            db.session.add(LoadLog(
                table_name = 'hadoop_log_jawn',
                hour = datetime(2014, 6, 20, 15, 0, 0, 0, pytz.UTC),
                version = "v001",
                load_time = 12.0,
                size_mb = 13.0,
                hostname = 'agg.jawn.prod2',
                last_run = datetime(2014, 6, 20, 15, 15, 0 , 0, pytz.UTC),
                data_source = 'hadoop_quest',
                good_records = 3,
                bad_records = 4)
            )

            # log_status for the hour we're testing, will be kept
            db.session.add(LogStatus(
                hour = datetime(2014, 6, 20, 15, 0, 0, 0, pytz.UTC),
                log_table = 'hadoop_log_jawn',
                version = "v001",
                hostname = 'jawn.jawn.jawn',
                load_complete = True,
                last_run = datetime(2014, 6, 20, 16, 10, 11, 0, pytz.UTC),
                data_source = 'hadoop_quest')
            )

            # won't be kept
            db.session.add(LogStatus(
                hour = datetime(2014, 6, 19, 15, 0, 0, 0, pytz.UTC),
                log_table = 'hadoop_log_not_jawn',
                version = 'v666',
                hostname = 'nojawn.nojawn.nojawn',
                load_complete = False,
                last_run = datetime(2014, 6, 06, 06, 0, 0, 0, pytz.UTC),
                data_source = 'hadoop_cypress')
            )

            db.session.add(State(
                hour = datetime(2014, 6, 20, 15, 0, 0, 0, pytz.UTC),
                table_name = 'hadoop_log_jawn',
                version = "v001",
                last_run = datetime(2014, 6, 20, 16, 10, 11, 0, pytz.UTC),
                hour_closed = True,
                data_source = 'hadoop_quest')
            )

            db.session.commit()
        except Exception, e:
            #db.session.rollback()
            raise e

        resp = self.app.get('/load_log?table_name=hadoop_log_jawn&data_source=hadoop_quest&hour=2014-06-20+15%3A00%3A00')
        self.assertEquals(200, resp.status_code)
        html = ElementTree.fromstring(resp.data)

        totals = html.findall('.//*[@id="totals"]')
        assert totals[0].find('.//*[@id="totals_good"]').text == '4'
        assert totals[0].find('.//*[@id="totals_bad"]').text == '6'
        assert totals[0].find('.//*[@id="totals_total"]').text == '10'
        assert totals[0].find('.//*[@id="totals_size"]').text == '23.0'
        assert totals[0].find('.//*[@id="totals_percent"]').text == '60.0'

        load_log_rows = html.findall('.//*[@class="load_log_row"]')
        assert len(load_log_rows) == 2

        # expecting order
        assert load_log_rows[1].find('.//*[@class="load_log_hour"]').text == '2014-06-20 15:00:00'
        assert load_log_rows[1].find('.//*[@class="load_log_last_run"]').text == '2014-06-20 15:10:00'
        assert load_log_rows[1].find('.//*[@class="load_log_size_mb"]').text == '10.0'
        assert load_log_rows[1].find('.//*[@class="load_log_version"]').text == 'v001'
        assert load_log_rows[1].find('.//*[@class="load_log_load_time"]').text == '11.0'
        assert load_log_rows[1].find('.//*[@class="load_log_data_source"]').text == 'hadoop_quest'
        assert load_log_rows[1].find('.//*[@class="load_log_good_records"]').text == '1'
        assert load_log_rows[1].find('.//*[@class="load_log_bad_records"]').text == '2'

        assert load_log_rows[0].find('.//*[@class="load_log_hour"]').text == '2014-06-20 15:00:00'
        assert load_log_rows[0].find('.//*[@class="load_log_last_run"]').text == '2014-06-20 15:15:00'
        assert load_log_rows[0].find('.//*[@class="load_log_size_mb"]').text == '13.0'
        assert load_log_rows[0].find('.//*[@class="load_log_version"]').text == 'v001'
        assert load_log_rows[0].find('.//*[@class="load_log_load_time"]').text == '12.0'
        assert load_log_rows[0].find('.//*[@class="load_log_data_source"]').text == 'hadoop_quest'
        assert load_log_rows[0].find('.//*[@class="load_log_good_records"]').text == '3'
        assert load_log_rows[0].find('.//*[@class="load_log_bad_records"]').text == '4'

        log_status_rows = html.findall('.//*[@class="log_status"]')
        assert len(log_status_rows) == 1

        assert log_status_rows[0].find('.//*[@class="log_status_hour"]').text == '2014-06-20 15:00:00'
        assert log_status_rows[0].find('.//*[@class="log_status_data_source"]').text == 'hadoop_quest'
        assert log_status_rows[0].find('.//*[@class="log_status_hostname"]').text == 'jawn.jawn.jawn'
        assert log_status_rows[0].find('.//*[@class="log_status_version"]').text == 'v001'
        # XXX: is this a boolean or int in mysql?
        assert log_status_rows[0].find('.//*[@class="log_status_load_complete"]').text == 'True'
        assert log_status_rows[0].find('.//*[@class="log_status_last_run"]').text == '2014-06-20 16:10:11'

        state_rows = html.findall('.//*[@class="state_row"]')
        assert state_rows[0].find('.//*[@class="state_hour"]').text == '2014-06-20 15:00:00'
        assert state_rows[0].find('.//*[@class="state_table_name"]').text == 'hadoop_log_jawn'
        assert state_rows[0].find('.//*[@class="state_data_source"]').text == 'hadoop_quest'
        assert state_rows[0].find('.//*[@class="state_version"]').text == 'v001'
        assert state_rows[0].find('.//*[@class="state_last_run"]').text == '2014-06-20 16:10:11'
        assert state_rows[0].find('.//*[@class="state_hour_closed"]').text == 'True'

if __name__ == '__main__':
    import unittest
    unittest.main()
