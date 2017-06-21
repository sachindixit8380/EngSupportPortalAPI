from unittest import TestCase
import datetime

from utils.endpoint_utils import return_sanitized_int, get_hour_from_string
from endpoints.exception import BadRequestException

class EndpointUtilsTest(TestCase):

    def test_sanitized_int_returns_int_from_string(self):
        sanitized_int = return_sanitized_int('1', 'wat')
        assert sanitized_int == 1

    def test_sanitized_int_throws_exception_for_bad_value(self):
        self.assertRaises(BadRequestException, return_sanitized_int, 'break_stuff', 'wat')

    def test_get_hour_returns_correct_datetime(self):
        timestamp = get_hour_from_string('1987-08-11 00:00')
        assert timestamp == datetime.datetime(1987, 8, 11)

    def test_get_hour_throws_exception_for_bad_hour(self):
        self.assertRaises(ValueError, get_hour_from_string, 'time is an illusion')

if __name__ == "__main__":
    unittest.main()
