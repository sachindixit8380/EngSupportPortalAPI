import pytest

from mock import Mock
from unittest import TestCase

from utils.auth.cached_authenticator import CachedAuthenticator
from utils.auth.exceptions import AuthException, InvalidSessionException


class TestCachedAuthenticator(TestCase):

    def setUp(self):
        self.mock_authenticator = Mock()
        self.mock_authenticator.verify_credentials = Mock()

        self.mock_groups = ["jungle", "book"]

        self.under_test = CachedAuthenticator(self.mock_authenticator)

    def test_authenticate_user_will_raise_exception(self):
        self.mock_authenticator.verify_credentials.side_effect = AuthException

        with pytest.raises(AuthException):
            self.under_test.authenticate_user('marco', 'polo')

    def test_authenticate_user_caches_valid_credentials(self):
        self.mock_authenticator.verify_credentials.return_value = "session_id"
        self.mock_authenticator.retrieve_groups.return_value = self.mock_groups

        # call authenticate user once to cache creds
        self.assertEquals(self.under_test.authenticate_user('king', 'kong'),
                          ('king', self.mock_groups, 'session_id'))

        # call verify session to make sure that session is cached
        self.assertEquals(self.under_test.verify_session('session_id'),
                          ('king', self.mock_groups, 'session_id'))


    def test_authenticator_will_reject_invalid_credentials_from_cache(self):
        self.mock_authenticator.verify_credentials.return_value = "session_id"
        self.mock_authenticator.retrieve_groups.return_value = self.mock_groups

        # Call authenticate first time to cache creds
        self.assertEquals(self.under_test.authenticate_user('king', 'kong'),
                          ('king', self.mock_groups, 'session_id'))
        # call verify session to make sure that session is cached
        self.assertEquals(self.under_test.verify_session('session_id'),
                          ('king', self.mock_groups, 'session_id'))

        # call with wrong session id to make sure that we see an error
        with pytest.raises(InvalidSessionException) as ex:
            self.under_test.verify_session('session_ig')
        self.assertEquals(ex.value.message, "Invalid session ID provided")

        # call verify session to make sure that session is still cached
        self.assertEquals(self.under_test.verify_session('session_id'),
                          ('king', self.mock_groups, 'session_id'))


    def test_verify_credentials_handles_multiple_users_safely(self):
        self.mock_authenticator.verify_credentials.return_value = "session_id"
        self.mock_authenticator.retrieve_groups.return_value = self.mock_groups

        self.assertEquals(self.under_test.authenticate_user('marco', 'yolo'),
                          ('marco', self.mock_groups, 'session_id'))
        self.assertEquals(self.under_test.verify_session('session_id'),
                          ('marco', self.mock_groups, 'session_id'))

        self.mock_authenticator.verify_credentials.return_value = "session_id_1"
        self.assertEquals(self.under_test.authenticate_user('king', 'kong'),
                          ('king', self.mock_groups, 'session_id_1'))
        self.assertEquals(self.under_test.verify_session('session_id_1'),
                          ('king', self.mock_groups, 'session_id_1'))

        # Ensure that the session IDs for all users are still in cache
        self.assertEquals(self.under_test.verify_session('session_id'),
                          ('marco', self.mock_groups, 'session_id'))
        self.assertEquals(self.under_test.verify_session('session_id_1'),
                          ('king', self.mock_groups, 'session_id_1'))
