import unittest
from mock import patch

from utils import vertica_utils

class VerticaUtilsTest(unittest.TestCase):

    def test_get_connection_for_data_source_fails_on_missing_config(self):
        with self.assertRaises(Exception) as cm:
            vertica_utils.get_connection_for_data_source({}, 'ramrod')
        assert 'ramrod is not a vertica cluster name' == cm.exception.message

    @patch('utils.vertica_utils.connect')
    def test_get_connection_for_data_source_passes_through_connect_failure(self, mock_connect):
        config = {
            'VERTICA': {
                'fakecluster': {
                    'user': 'notuseddontcare'
                }
            }
        }
        some_exception = Exception('your connection is bad and you should feel bad')

        mock_connect.side_effect = some_exception
        with self.assertRaises(Exception) as cm:
            vertica_utils.get_connection_for_data_source(config, 'fakecluster')

        # XXX: the vertia python code doesn't really document what can go wrong,
        #      so make sure we just pass through whatever exception it raises
        assert some_exception is cm.exception

    @patch('utils.vertica_utils.connect')
    def test_get_connection_for_data_source_does_as_advertised(self, mock_connect):
        config = {
            'VERTICA': {
                'fakecluster': {
                    'user': 'notuseddontcare'
                }
            }
        }

        mock_connect_result = 'ducktyping ftw, this is in theory a connection'
        mock_connect.return_value = mock_connect_result

        # testing for sameness here
        assert mock_connect_result is \
            vertica_utils.get_connection_for_data_source(config, 'fakecluster')

        mock_connect.assert_called_once_with(config['VERTICA']['fakecluster'])
