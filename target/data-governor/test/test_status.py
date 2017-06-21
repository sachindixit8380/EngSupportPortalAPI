from socket import gethostname
from mock import patch

from test.test_base import EndpointTest
from endpoints.status import StatusEndpoint

class StatusEndpointTest(EndpointTest):

    def test_get_status_returns_200_and_minimal_metadata(self):
        response = self.app.get('/status')
        self.assertEquals(200, response.status_code)
        self.assertTrue('STATUS: UP' in response.data)
        self.assertTrue('HOST: {}'.format(gethostname()) in response.data)

    @patch('endpoints.status.isfile')
    def test_get_status_returns_503_and_minimal_metadata(self, mock_is_file):
        mock_is_file.return_value = True

        response = self.app.get('/status')
        self.assertEquals(503, response.status_code)
        self.assertTrue('STATUS: DOWN' in response.data)
        self.assertTrue('HOST: {}'.format(gethostname()) in response.data)

        mock_is_file.assert_called_once_with('/etc/data-governor-disable')
