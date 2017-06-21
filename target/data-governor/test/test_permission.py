"""Tests for the scheduler stats endpoint"""
from xml.etree import ElementTree
from mock import patch
import unittest

from endpoints.permission import PermissionEndpoint
from test.test_base import EndpointTest
from endpoints import app
from endpoints.database import db, DMFBase, DgUserPermission
from endpoints.exception import ForbiddenException
from utils.permission_utils import PERMISSIBLE_ACTIONS,\
                                   get_permitted_actions


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class PermissionEndpointTest(EndpointTest):

    def setUp(self):
        super(PermissionEndpointTest, self).setUp()
        self.db = db
        DMFBase.metadata.create_all(db.engine)

        username='test_user_one'
        try:
            user_permission_one = DgUserPermission(
                id=1,
                username=username,
                permitted_actions = '')

            db.session.add(user_permission_one)
            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)

    def test_permission_get_success(self):
        response = self.app.get('/permission')
        assert response.status_code == 200

    def test_permission_get_selected_user_one_success(self):
        response = self.app.get('/permission?selected_user=test_user_one')
        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        check_boxes = html.findall('.//*[@class="permitted_action_checkboxes"]')
        check_box_inputs = [ (check_box.attrib['name'], check_box.attrib['value']) for check_box in check_boxes ]
        assert len(check_box_inputs) == 1
        assert (('user_permissions', 'close_vertica_session') in check_box_inputs)

    def test_user_can_see_only_navbar_tabs_they_have_permission_for(self):
        """ FIXME: This test might not be necessary once we get rid of permissions
        """
        app.config['PERMISSION_ENABLED'] = True
        response = self.app.get('/permission')
        assert response.status_code == 200
        app.config['PERMISSION_ENABLED'] = False

    def test_permission_get_selected_user_two_success(self):
        response = self.app.get('/permission?selected_user=test_user_two')
        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        check_boxes = html.findall('.//*[@type="checkbox"]')
        assert len(check_boxes) == 4

    @patch('endpoints.permission.check_membership')
    def test_permission_post_not_permitted_user_cannot_update_permission(self, mock_check_membership):
        mock_check_membership.side_effect=ForbiddenException("user not permitted")
        response = self.app.post('/permission')
        assert response.status_code == 403

    def test_permission_post_update_permissions_success_redirect_response(self):
        test_user_one = 'test_user_one'
        self.mock_perm_g.permissions = get_permitted_actions(db.session, test_user_one)
        new_permission_data = {'user_permissions':[PERMISSIBLE_ACTIONS['CLOSE_VERTICA_SESSION']]}
        response = self.app.post('/permission?selected_user={0}'.format(test_user_one), data=new_permission_data)
        assert response.status_code == 302

        new_permitted_actions = get_permitted_actions(db.session, test_user_one)
        assert len(new_permitted_actions) == 1
        assert PERMISSIBLE_ACTIONS['CLOSE_VERTICA_SESSION'] in new_permitted_actions

    def test_permission_post_update_permissions_to_none_success_redirect_response(self):
        test_user_one = 'test_user_one'
        self.mock_perm_g.permissions = get_permitted_actions(db.session, test_user_one)
        # XXX: empty user_permissions = no user_permissions key/vals
        new_permission_data = {}
        response = self.app.post('/permission?selected_user={0}'.format(test_user_one), data=new_permission_data)
        assert response.status_code == 302

        new_permitted_actions = get_permitted_actions(db.session, test_user_one)
        assert new_permitted_actions == []

if __name__ == '__main__':
    import unittest
    unittest.main()
