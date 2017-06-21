from endpoints.system_info import SystemInfoEndpoint

from test.test_base import EndpointTest

class SystemInfoEndpointTests(EndpointTest):

    def test_get_view_status_returns_200(self):
        response = self.app.get('/system-info')
        self.assertEquals(200, response.status_code)
