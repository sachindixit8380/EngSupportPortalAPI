import json
from mock import patch, Mock

from endpoints.job_conflict import JobConflictEndpoint
from endpoints import app
from endpoints.database import db, DMFBase
from test.test_base import EbeeEndpointTest

app.config['EBEE_API_BASE'] = 'https://some_url'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.testing = True

class JobConflictTest(EbeeEndpointTest):

    def setUp(self):
        super(JobConflictTest, self).setUp()

        self.db = db
        DMFBase.metadata.create_all(db.engine)
        self.flask_app = app
        session = db.session()

        self.requests_patcher = patch('utils.ebee_client.requests')
        self.auth_patcher = patch('utils.requests_utils.HTTPBasicAuth')

        self.mock_requests = self.requests_patcher.start()
        self.mock_auth = self.auth_patcher.start()

    def tearDown(self):
        self.requests_patcher.stop()
        self.auth_patcher.stop()
        DMFBase.metadata.drop_all(db.engine)
        super(JobConflictTest, self).tearDown()

    @patch('endpoints.job_conflict.url_for')
    def test_valid_post(self, mock_url_for):
        valid_data = {'job_name': 'liquor',
                      'data_source': 'brown_paper_bag',
                      'conflicting_job_name': 'beer',
                      'conflicting_data_source': 'bar'}

        self.mock_requests.post.return_value = mock_resp(201, 'some_response')
        self.mock_auth.return_value = 'foo'

        payload = {'name': valid_data['job_name'],
                   'dataSource': valid_data['data_source'],
                   'conflictingName': valid_data['conflicting_job_name'],
                   'conflictingDataSource': valid_data['conflicting_data_source']}
        headers = {'content-type':'application/json'}
        headers.update(self.ebee_delegation_headers)

        response = self.app.post('/job_conflict', data=valid_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        url = 'https://some_url/jobs/liquor/schedules/brown_paper_bag/conflicts'
        self.mock_requests.post.assert_called_with(url=url,
                                                     data=json.dumps(payload),
                                                     headers=headers,
                                                     timeout=15,
                                                     verify=False,
                                                     auth='foo',
                                                     params=None)

    @patch('endpoints.job_conflict.url_for')
    def test_valid_delete(self, mock_url_for):
        delete_data = {'_method': 'DELETE',
                       'job_name': 'beer',
                       'data_source': 'bar',
                       'conflicting_job_name': 'burger',
                       'conflicting_data_source': 'brown_paper_bag'}
        self.mock_requests.delete.return_value = mock_resp(200, 'some_response')
        self.mock_auth.return_value = 'foo'

        headers = self.ebee_delegation_headers

        response = self.app.post('/job_conflict', data=delete_data)
        assert response.status_code == 302
        mock_url_for.assert_called_with('job_control')
        url = 'https://some_url/jobs/beer/schedules/bar/conflicts/burger/dataSources/brown_paper_bag'
        self.mock_requests.delete.assert_called_with(url=url,
                                                     timeout=15,
                                                     verify=False,
                                                     auth='foo',
                                                     params=None,
                                                     headers=headers)

def mock_resp(code, data):
    mock_resp = Mock()
    mock_resp.status_code = code
    mock_resp.json.return_value = data
    return mock_resp
