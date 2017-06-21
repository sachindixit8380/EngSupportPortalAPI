"""Tests for the "/audit_log_search" endpoint"""

from datetime import datetime
from xml.etree import ElementTree

from test.test_base import EndpointTest
from endpoints.audit_log_search import AuditLogSearchEndpoint
from endpoints.database import db, DMFBase, DgAuditLog
from endpoints import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class AuditLogSearchEndpointTests(EndpointTest):

    def setUp(self):
        super(AuditLogSearchEndpointTests, self).setUp()
        DMFBase.metadata.create_all(db.engine)
        session = db.session()

        try:
            entry_0 = DgAuditLog(
                ymdh=datetime(2015, 04, 20, 10, 0, 0),
                user='bokelley',
                message='i done goofed')

            entry_1 = DgAuditLog(
                ymdh=datetime(2015, 04, 21, 10, 0, 0),
                user='bokelley',
                message='data team rocks')

            entry_2 = DgAuditLog(
                ymdh=datetime(2015, 04, 22, 10, 0, 0),
                user='jlee1',
                message='cool feature dude')

            session.add(entry_0)
            session.add(entry_1)
            session.add(entry_2)
            session.commit()
        except Exception, e:
            print e
            session.rollback()
            self.tearDown()

    def tearDown(self):
        DMFBase.metadata.drop_all(db.engine)
        super(AuditLogSearchEndpointTests, self).tearDown()

    def test_get_method_with_no_search_params(self):
        response = self.app.get('/audit_log_search')
        assert response.status_code == 200

    def test_search_for_user(self):
        response = self.app.get('/audit_log_search?user=jlee1&message_filter=&timestamp_from=&timestamp_to=')
        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        assert html.find('.//span[@class="timestamp"]').text == '2015-04-22 10:00:00'
        assert html.find('.//span[@class="user"]').text == 'jlee1'
        assert 'cool feature dude' in html.find('.//span[@class="msg"]').text

    def test_search_for_message(self):
        response = self.app.get('/audit_log_search?user=&message_filter=data&timestamp_from=&timestamp_to=')
        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        assert html.find('.//span[@class="timestamp"]').text == '2015-04-21 10:00:00'
        assert html.find('.//span[@class="user"]').text == 'bokelley'
        assert 'data team rocks' in html.find('.//span[@class="msg"]').text

    def test_search_with_timestamp(self):
        response = self.app.get('/audit_log_search?user=&message_filter=&timestamp_from=2015-04-20+10%3A00%3A00&timestamp_to=')
        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        assert html.findall('.//span[@class="timestamp"]')[0].text == '2015-04-22 10:00:00'
        assert html.findall('.//span[@class="timestamp"]')[1].text == '2015-04-21 10:00:00'
        assert html.findall('.//span[@class="timestamp"]')[2].text == '2015-04-20 10:00:00'
        assert html.findall('.//span[@class="user"]')[0].text == 'jlee1'
        assert html.findall('.//span[@class="user"]')[1].text == 'bokelley'
        assert html.findall('.//span[@class="user"]')[2].text == 'bokelley'
        assert 'cool feature dude' in html.findall('.//span[@class="msg"]')[0].text
        assert 'data team rocks' in html.findall('.//span[@class="msg"]')[1].text
        assert 'i done goofed' in html.findall('.//span[@class="msg"]')[2].text

    def test_search_with_all_filters(self):
        response = self.app.get('/audit_log_search?user=bokelley&message_filter=done+goofed&timestamp_from=2015-04-20+10%3A00%3A00&timestamp_to=2015-04-20+12%3A00%3A00')
        assert response.status_code == 200
        html = ElementTree.fromstring(response.data)
        assert html.find('.//span[@class="timestamp"]').text == '2015-04-20 10:00:00'
        assert html.find('.//span[@class="user"]').text == 'bokelley'
        assert 'i done goofed' in html.find('.//span[@class="msg"]').text
