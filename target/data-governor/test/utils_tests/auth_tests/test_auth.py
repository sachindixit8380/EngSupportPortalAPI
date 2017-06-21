
from werkzeug.datastructures import Authorization

from mock import Mock, patch
from unittest import TestCase

from endpoints import app
from utils.auth import AuthManager
from utils.auth.exceptions import AuthException, InvalidSessionException

class AuthManagerTest(TestCase):

    def setUp(self):
        self.mock_authenticator = Mock()
        self.under_test = AuthManager(authenticator=self.mock_authenticator)

        self.g_patcher = patch('utils.auth.auth.g')
        self.mock_g = self.g_patcher.start()

    def tearDown(self):
        self.g_patcher.stop()

    @patch('utils.auth.auth.request')
    def test_check_authorization_returns_None_and_sets_g_username_None_on_authless_endpoints(self, mock_request):
        self.under_test.set_authless_paths(['/static'])

        mock_request.path = '/static/some/buggy/javascript.js'

        self.assertEquals(None, self.under_test.check_authorized(app))

        self.assertEquals([], self.mock_authenticator.verify_credentials.mock_calls)
        self.assertEquals(None, self.mock_g.username)

    @patch('utils.auth.auth.request')
    def test_check_authorization_returns_401_if_request_has_no_authorization(self, mock_request):
        mock_request.authorization = None

        self.assertEquals(401, self.under_test.check_authorized(app).status_code)

    @patch('utils.auth.auth.request')
    def test_check_authorization_returns_401_if_request_has_invalid_credentials(self, mock_request):
        self.mock_authenticator.authenticate_user.side_effect = AuthException
        user_pass_dict = {'username': 'carmen', 'password': 'sandiego'}
        mock_request.authorization = Authorization('basic', user_pass_dict)

        self.assertEquals(401, self.under_test.check_authorized(app).status_code)

        self.mock_authenticator.authenticate_user.assert_called_with('carmen', 'sandiego')

    @patch('utils.auth.auth.request')
    def test_check_authorization_returns_None_and_sets_g_values_if_all_is_well(self, mock_request):
        self.mock_authenticator.authenticate_user.return_value = ("ron",
                                                                  ["group1", "group2"],
                                                                  "session_id")
        user_pass_dict = {'username': 'ron', 'password': 'burgundy'}
        mock_request.authorization = Authorization('basic', user_pass_dict)

        self.assertEquals(None, self.under_test.check_authorized(app))

        self.mock_authenticator.authenticate_user.assert_called_with('ron', 'burgundy')
        self.assertEquals('ron', self.mock_g.username)
        self.assertEquals(['group1', 'group2'], self.mock_g.user_groups)
        self.assertEquals('session_id',  self.mock_g.session_id)

    @patch('utils.auth.auth.request')
    def test_check_authorization_correctly_extracts_headers(self, mock_request):
        self.mock_authenticator.verify_session.return_value = ("ron",
                                                               ["group1", "group2"],
                                                               "session_id")
        mock_request.cookies = { AuthManager.DG_COOKIE_NAME: "session_id" }

        self.assertEquals(None, self.under_test.check_authorized(app))
        self.mock_authenticator.verify_session.assert_called_with('session_id')
        self.assertEquals('ron', self.mock_g.username)
        self.assertEquals(['group1', 'group2'], self.mock_g.user_groups)
        self.assertEquals('session_id',  self.mock_g.session_id)

    @patch('utils.auth.auth.request')
    def test_empty_cookie_value_throws_auth_exception(self, mock_request):
        mock_request.cookies = { AuthManager.DG_COOKIE_NAME: None }

        response = self.under_test.check_authorized(app)
        self.assertEquals(response.status, "401 UNAUTHORIZED")
        self.assertEquals(response.status_code, 401)
        self.assertEquals(response.response, ["Authentication required"])


    @patch('utils.auth.auth.request')
    def test_invalid_session_can_still_authenticate_with_username_password(self, mock_request):
        self.mock_authenticator.authenticate_user.return_value = ("ron",
                                                                  ["group1", "group2"],
                                                                  "session_id")
        self.mock_authenticator.verify_session.side_effect = InvalidSessionException

        mock_request.cookies = { AuthManager.DG_COOKIE_NAME: "session_id" }
        user_pass_dict = {'username': 'ron', 'password': 'burgundy'}
        mock_request.authorization = Authorization('basic', user_pass_dict)

        self.assertEquals(None, self.under_test.check_authorized(app))

        self.mock_authenticator.authenticate_user.assert_called_with('ron', 'burgundy')
        self.assertEquals('ron', self.mock_g.username)
        self.assertEquals(['group1', 'group2'], self.mock_g.user_groups)
        self.assertEquals('session_id',  self.mock_g.session_id)

    @patch('utils.auth.auth.request')
    def test_autoenv_admin_group_is_correctly_added_to_g(self, mock_request):
        autoenv_test = AuthManager(authenticator=self.mock_authenticator,
                                   config={'DPAAS_ADMIN_GROUP': 'autoenvAdmin'})

        self.mock_authenticator.authenticate_user.return_value = ("ron",
                                                                  ["group1", "group2"],
                                                                  "session_id")
        user_pass_dict = {'username': 'ron', 'password': 'burgundy'}
        mock_request.authorization = Authorization('basic', user_pass_dict)
        self.assertEquals(None, autoenv_test.check_authorized(app))

        self.assertEquals('ron', self.mock_g.username)
        self.assertEquals(['group1', 'group2', 'autoenvAdmin'], self.mock_g.user_groups)
        self.assertEquals('session_id',  self.mock_g.session_id)


if __name__ == '__main__':
    unittest.main()
