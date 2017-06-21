from mock import patch
from unittest import TestCase

from utils.permission_utils import is_permitted,\
                                   has_permission,\
                                   check_permission,\
                                   get_permitted_actions,\
                                   dg_user_permission_new_username,\
                                   dg_user_permission_update_permitted_actions,\
                                   is_member_of,\
                                   check_membership,\
                                   PERMISSIBLE_ACTIONS
from endpoints.database import db, DMFBase, DgUserPermission
from endpoints.exception import ForbiddenException
from sqlalchemy.exc import IntegrityError

class PermissionTest(TestCase):

    def setUp(self):
        super(PermissionTest, self).setUp()

        self.g_patcher = patch('utils.permission_utils.g')
        self.mock_g = self.g_patcher.start()

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        session = db.session()

        try:
            test_user_one = DgUserPermission(
                id=1,
                username='test_user_one',
                permitted_actions="{0}".format(PERMISSIBLE_ACTIONS['CLOSE_VERTICA_SESSION']))

            test_user_two = DgUserPermission(
                id=2,
                username='test_user_two',
                permitted_actions=','.join(PERMISSIBLE_ACTIONS.values()))

            test_user_three = DgUserPermission(
                id=3,
                username='test_user_three',
                permitted_actions='')

            session.add(test_user_one)
            session.add(test_user_two)
            session.add(test_user_three)
            session.commit()
        except Exception, e:
            print e
            session.rollback()
            self.tearDown()

    def tearDown(self):
        self.g_patcher.stop()
        DMFBase.metadata.drop_all(db.engine)
        super(PermissionTest, self).tearDown()

    def test_get_permitted_actions_returns_actions_attached_to_user_filtering_invalid_actions(self):
        session = self.db.session
        perms_str = ','.join([
            PERMISSIBLE_ACTIONS['CLOSE_VERTICA_SESSION'], 'fake_permission'
        ])
        session.add(DgUserPermission(username='jawndoe', permitted_actions=perms_str))
        session.commit()

        permitted_actions = get_permitted_actions(db.session, 'jawndoe')
        assert 1 == len(permitted_actions)
        assert PERMISSIBLE_ACTIONS['CLOSE_VERTICA_SESSION'] in permitted_actions
        assert 'fake_permission' not in permitted_actions

    def test_dg_user_permission_new_username_creates_single_user_with_blank_perms(self):
        dg_user_permission_new_username(db.session, 'brandnewyouser')
        users = db.session.query(DgUserPermission).filter(DgUserPermission.username=='brandnewyouser').all()
        assert 1 == len(users)
        assert '' == users[0].permitted_actions

    def test_dg_user_permission_cannot_overwrite_existing_user(self):
        session = self.db.session
        session.add(DgUserPermission(username='oldyouser', permitted_actions='fake_permission'))
        session.commit()
        self.assertRaises(IntegrityError, dg_user_permission_new_username, db.session, 'oldyouser')

    def test_dg_user_permission_update_permitted_actions_properly_updates_permissions_filtering_invalid(self):
        session = self.db.session
        perms_str = PERMISSIBLE_ACTIONS['CLOSE_VERTICA_SESSION']

        session.add(DgUserPermission(username='jawndoe', permitted_actions=perms_str))
        session.commit()

        new_actions = ['fake_permission']
        dg_user_permission_update_permitted_actions(db.session, 'jawndoe', new_actions)

        users = db.session.query(DgUserPermission).filter(DgUserPermission.username=='jawndoe').all()
        assert 1 == len(users)
        actions = users[0].permitted_actions.split(',')
        assert 1 == len(actions)

    def test_dg_user_permission_update_permitted_actions_cannot_update_nonexistent_user(self):
        new_actions = ['fake_permission']
        with self.assertRaises(Exception):
            dg_user_permission_update_permitted_actions(db.session, 'nosuchuser', new_actions)

    def test_has_permissions_returns_if_user_has_permission_when_enforcement_off(self):
        # XXX: bit flimsy, may want to raise permissions_enforced to a 'visible' method and mock
        self.mock_g.permission_enforced = False
        self.mock_g.permissions = ['sit']
        assert has_permission('sit')
        assert not has_permission('stay')

    def test_has_permissions_returns_if_user_has_permission_when_enforcement_on(self):
        # XXX: bit flimsy, may want to raise permissions_enforced to a 'visible' method and mock
        self.mock_g.permission_enforced = True
        self.mock_g.permissions = ['sit']
        assert has_permission('sit')
        assert not has_permission('stay')

    def test_check_permission_test_user_one(self):
        """is test_user_one permitted to close_vertica_sessions?
        """
        username = 'test_user_one'
        permitted_actions = get_permitted_actions(self.db.session, username)
        self.mock_g.permissions = set(permitted_actions)
        self.assertEquals(is_permitted(PERMISSIBLE_ACTIONS['CLOSE_VERTICA_SESSION']), True)

    def test_check_permission_test_user_two(self):
        """is test_user_two permitted to close vertica sessions?"""
        username = 'test_user_two'
        permitted_actions = get_permitted_actions(self.db.session, username)
        self.mock_g.permissions = set(permitted_actions)
        self.assertEquals(is_permitted(PERMISSIBLE_ACTIONS['CLOSE_VERTICA_SESSION']), True)


    def test_check_permission_test_user_three(self):
        """is test_user_three forbidden to close vertica sessions"""
        username = 'test_user_three'
        permitted_actions = get_permitted_actions(self.db.session, username)
        self.mock_g.permissions = set(permitted_actions)
        with self.assertRaises(ForbiddenException):
            check_permission(PERMISSIBLE_ACTIONS['CLOSE_VERTICA_SESSION'])

    def test_check_permission_test_user_four(self):
        """is test_user_three forbidden to ignore_late_data, edit_job, and edit_state?"""
        username = 'test_user_four'
        permitted_actions = get_permitted_actions(self.db.session, username)
        self.mock_g.permissions = set(permitted_actions)
        with self.assertRaises(ForbiddenException):
            check_permission(PERMISSIBLE_ACTIONS['CLOSE_VERTICA_SESSION'])

    def test_is_permitted_returns_true_if_no_permissions_are_set(self):
        self.mock_g.permission_enforced = True
        self.mock_g.permissions = None

        assert is_permitted('lets fly the Falcon X')

    def test_is_member_of_checks_membership_correctly(self):
        self.mock_g.user_groups = ["tatooine", "klingon"]
        assert is_member_of("tatooine")
        assert is_member_of("klingon")

        assert not is_member_of("earth")

    def test_check_membership_returns_nothing_if_user_is_a_member(self):
        self.mock_g.user_groups = ["tatooine", "klingon"]
        self.assertIsNone(check_membership("tatooine"))
        self.assertIsNone(check_membership("klingon"))

    def test_check_membership_raises_exception_when_user_is_not_a_member(self):
        self.mock_g.user_groups = ["tatooine", "klingon"]
        with self.assertRaises(ForbiddenException):
            check_membership("earth")
        with self.assertRaises(ForbiddenException):
            check_membership("naboo")

    def test_is_member_of_returns_false_if_user_groups_is_not_set(self):
        assert not is_member_of("earth")
        assert not is_member_of("tatooine")

if __name__ == '__main__':
    unittest.main()
