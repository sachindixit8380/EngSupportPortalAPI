import datetime
from mock import patch, MagicMock
from xml.etree import ElementTree

from endpoints.vertica_sessions import VerticaSessionsEndpoint
from test.test_base import EndpointTest
from endpoints import app

app.testing = True

class VerticaSessionsEndpointTest(EndpointTest):

    LOCK_ROWS = 'endpoints.vertica_sessions.VerticaSessionsEndpoint._get_lock_rows_from_vertica_host'
    VERT_CONN = 'endpoints.vertica_sessions.get_connection_for_data_source'

    def setUp(self):
        super(VerticaSessionsEndpointTest, self).setUp()
        self.vertica_lock_row_response = [{
          'lock_mode': 'I',
          'request_timestamp': datetime.datetime(2015, 1, 22, 0, 52, 57, 764618),
          'session_id': '208.bm-vertica.prod-15304:0x189443e',
          'object_name': 'Table:public.agg_platform_michael_anzuoni_is_a_god_amongst_mortals',
          'transaction_description': "Txn: 1b00000003cc430 'select * from lol limit 420'",
          'host': 'vertica_warreng'}]

    @patch(LOCK_ROWS)
    def test_endpoint_is_up(self, mock_lock_rows):
        mock_lock_rows.return_value = self.vertica_lock_row_response 
        response = self.app.get('/vertica_sessions')
        assert response.status_code == 200

    @patch(LOCK_ROWS)
    def test_endpoint_returns_proper_rows(self, mock_lock_rows):
        mock_lock_rows.return_value = self.vertica_lock_row_response 
        response = self.app.get('/vertica_sessions')
        html = ElementTree.fromstring(response.data)
        assert html.findall('.//*[@class="host"]')[0].text == 'vertica_warreng'
        assert html.findall('.//*[@class="lock_mode"]')[0].text == 'I'
        assert html.findall('.//*[@class="session_id"]')[0].text == '208.bm-vertica.prod-15304:0x189443e'
        assert html.findall('.//*[@class="request_timestamp"]')[0].text == '2015-01-22 00:52:57.764618'
        assert html.findall('.//*[@class="transaction_description"]')[0].text == "Txn: 1b00000003cc430 'select * from lol limit 420'"
        assert html.findall('.//*[@class="object_name"]')[0].text == 'Table:public.agg_platform_michael_anzuoni_is_a_god_amongst_mortals'

    @patch(VERT_CONN)
    def test_delete_method_works(self, mock_vert):
        mock_vert.return_value = MagicMock()
        result_mock = MagicMock()
        result_mock.rows[0] = {"close_session": "lol yep its done"}
        mock_vert.query.return_value = result_mock
        response = self.app.post('/vertica_sessions', data={'host': 'vertica_camron', '_method': 'DELETE', 'session_id': '208.bm-vertica.prod-15304:0x189443e'})
        assert response.status_code == 302
