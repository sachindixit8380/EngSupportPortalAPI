from unittest import TestCase
from mock import patch

from endpoints.base import Endpoint
from utils.view_factory import ViewFactory


class ViewFactoryTest(TestCase):

    @patch('endpoints.base.Endpoint.as_view')
    def test_config_not_supplied_when_constructor_has_no_config_arg(self, mock_as_view):
        # XXX: hacked up inline class since we can't mock __init__
        class FauxEndpoint(Endpoint):
            __view_name__ = "wanderer"
            def __init__(self):
                pass

        ViewFactory({}).create_for(FauxEndpoint)

        mock_as_view.assert_called_with("wanderer")


    @patch('endpoints.base.Endpoint.as_view')
    def test_config_supplied_when_constructor_has_config_arg(self, mock_as_view):
        # XXX: hacked up inline class since we can't mock __init__
        class FauxEndpoint(Endpoint):
            __view_name__ = "builder"
            def __init__(self, config):
                pass

        config = { "moretraps": "to catch more creatures" }

        ViewFactory(config).create_for(FauxEndpoint)

        mock_as_view.assert_called_with("builder", config=config)


if __name__ == "__main__":
    unittest.main()
