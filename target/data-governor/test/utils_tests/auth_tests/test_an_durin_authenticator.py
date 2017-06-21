
import json
import pytest
from mock import patch, Mock
from requests import Response
from endpoints import app
from endpoints.exception import ServerErrorException
from test.test_base import EndpointTest
from utils.auth.an_durin_authenticator import ANDurinAuthenticator
from utils.auth.exceptions import AuthException

app.config['AUTH_API_BASE'] = "https://some-dummy-url"

class ANDurinAuthenticatorTest(EndpointTest):

    def setUp(self):
        super(ANDurinAuthenticatorTest, self).setUp()

        self.requests_patcher = patch('utils.auth.an_durin_authenticator.requests')
        self.mock_requests = self.requests_patcher.start()
        self.mock_requests.post = Mock()

        self.under_test = ANDurinAuthenticator(app.config)

    def tearDown(self):
        self.mock_requests = self.requests_patcher.stop()
        super(ANDurinAuthenticatorTest, self).tearDown()

    def test_verify_credentials_throws_exception_on_invalid_username(self):
        with pytest.raises(AuthException):
            self.under_test.verify_credentials("", "password")

    def test_verify_credentials_properly_marshalls_request(self):
        mock_response = Response
        mock_response.status_code = 404
        self.mock_requests.post.return_value = mock_response

        with pytest.raises(AuthException):
            self.under_test.verify_credentials('han', 'solo')

        args, kw_args = self.mock_requests.post.call_args

        self.assertEquals("https://some-dummy-url/authenticate", kw_args['url'])
        self.assertEquals({'auth': {'username': 'han', 'password': 'solo', 'authDomain': 'people'}},\
                          json.loads(kw_args['data']))

    def test_verify_credentials_correctly_extracts_session_id(self):
        mock_response = Response
        mock_response.status_code = 200
        mock_response.content = "{\"response\": {\"id\":\"millenium_falcon\"}}"
        self.mock_requests.post.return_value = mock_response

        self.assertEquals(self.under_test.verify_credentials('han', 'solo'),
                          "millenium_falcon")

        args, kw_args = self.mock_requests.post.call_args
        self.assertEquals("https://some-dummy-url/authenticate", kw_args['url'])

    def test_verify_credentials_throws_server_error_exception(self):
        self.mock_requests.post.side_effect = Exception

        with pytest.raises(ServerErrorException):
            self.under_test.verify_credentials('han', 'solo')

    def test_retrieve_groups_correctly_retrieves_groups(self):
        mock_response = Response
        mock_response.status_code = 200
        mock_response.content = "{\"response\": {\"groups\":[\"tatooine\", \"naboo\"]}}"
        self.mock_requests.get.return_value = mock_response

        self.assertEquals(self.under_test.retrieve_groups("hansolo"),
                          ["tatooine", "naboo"])

    def test_retrieve_groups_throws_exception_on_invalid_username(self):
        with pytest.raises(AuthException):
            self.under_test.retrieve_groups("")

    def test_retrieve_groups_correctly_sets_path_parameters(self):
        mock_response = Response
        mock_response.status_code = 404
        self.mock_requests.get.return_value = mock_response

        with pytest.raises(AuthException):
            self.under_test.retrieve_groups("hansolo")

        args, kw_args = self.mock_requests.get.call_args
        self.assertEquals("https://some-dummy-url/permissions/hansolo/authDomains/people/service/data-governor",
                          kw_args['url'])

    def test_retrieve_groups_throws_server_error_exception(self):
        self.mock_requests.get.side_effect = Exception

        with pytest.raises(ServerErrorException):
            self.under_test.retrieve_groups("hansolo")
