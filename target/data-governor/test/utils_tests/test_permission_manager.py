from unittest import TestCase
from mock import patch

from utils.permission import PermissionManager
from endpoints import app
from endpoints.database import db, DMFBase, DgUserPermission

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class PermissionManagerTest(TestCase):

    def setUp(self):
        self.test_permission_manager = PermissionManager(app.config)
        self.g_patcher = patch('utils.permission.permission_manager.g')
        self.mock_g = self.g_patcher.start()
        DMFBase.metadata.create_all(db.engine)

        try:
            existing_user = DgUserPermission(id=1,
                                             username='existing_user',
                                             permitted_actions='ignore_late_data,pause_job')
    
            db.session.add(existing_user)
            db.session.commit()
        except Exception, e:
            print e
            db.session.rollback()
            self.tearDown()

    def tearDown(self):
        self.g_patcher.stop()
        DMFBase.metadata.drop_all(db.engine)

    @patch('utils.permission.permission_manager.get_permitted_actions')
    def test_permission_manager_sets_g(self, mock_get_permitted_actions):
        test_user = 'test_user'
        mock_get_permitted_actions.return_value=set(['pause_job', 'ignore_late_data'])
        self.test_permission_manager.populate_permissions_on_g(test_user)
        mock_get_permitted_actions.assert_called_with(db.session, test_user)
        assert len(self.mock_g.permissions) == 2
        assert 'ignore_late_data' in self.mock_g.permissions
        assert 'pause_job' in self.mock_g.permissions

    def test_permission_manager_creates_new_user(self):
        new_user = 'new_user'
        self.test_permission_manager.create_user_if_not_exist(new_user)
        new_user_permission = db.session.query(DgUserPermission).\
            filter(DgUserPermission.username==new_user).one()
        assert new_user_permission
        assert new_user_permission.permitted_actions == ''

    def test_permission_manager_doesnt_modify_existing_user(self):
        existing_user = 'existing_user'
        self.test_permission_manager.create_user_if_not_exist(existing_user)
        existing_user_permission = db.session.query(DgUserPermission).\
            filter(DgUserPermission.username==existing_user).one()
        assert existing_user_permission
        assert existing_user_permission.permitted_actions == 'ignore_late_data,pause_job'
