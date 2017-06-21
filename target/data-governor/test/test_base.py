"""Base test class for all endpoint tests."""

import unittest

from endpoints import app
from mock import patch

# importing globals injects needed functions and variables into jinja
import endpoints.globals

class EndpointTest(unittest.TestCase):
    """Base class for endpoint tests."""

    def setUp(self):
        """Set up tasks."""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()

        # These user_groups are necessary for checking permissions
        self.user_groups = ["dpaas_admin_rw"]
        # Patch the g import in permission_utils
        self.perm_g_patcher = patch('utils.permission_utils.g')
        self.mock_perm_g = self.perm_g_patcher.start()
        # Setup per request user_groups
        self.mock_perm_g.user_groups = self.user_groups

        # Turn off permission enforcement explicitly
        self.mock_perm_g.permission_enforced = False

    def tearDown(self):
        """Tear down tasks."""
        self.perm_g_patcher.stop()
        self.app = None


class EbeeEndpointTest(EndpointTest):
    """ Base class for all Ebee Endpoint tests """

    def setUp(self):
        """ Setup tasks """
        super(EbeeEndpointTest, self).setUp()

        # These headers need to be sent to Ebee at all times
        self.username = 'awesome_user'
        self.session_id = 'best_session_ever'
        self.ebee_delegation_headers = {'X-Delegate-User': self.username,
                                        'X-Delegate-User-Token': self.session_id}

        self.ebee_g_patcher = patch('utils.requests_utils.g')
        self.mock_ebee_g = self.ebee_g_patcher.start()

        # Setup per-request username and session id
        self.mock_ebee_g.username = self.username
        self.mock_ebee_g.session_id = self.session_id

    def tearDown(self):
        self.ebee_g_patcher.stop()
        super(EbeeEndpointTest, self).tearDown()
