"""Tests for running the application"""

import unittest
import subprocess


class RunApplicationTests(unittest.TestCase):
    """Tests the basic functionality of the application."""

    @staticmethod
    def test_without_manager_defined():
        """Will the application start if a SERVICE_MANAGER is not
        defined using an environment variable?"""
        try:
            process = subprocess.check_output(['python', 'runserver.py'],
                    env={},
                    stderr=subprocess.STDOUT,
                    shell=True)
        except subprocess.CalledProcessError as error:
            assert error.returncode != 0
            assert 'KeyError: None' in process.output
            assert 'JOB_MANAGER_IMPLEMENTATION' in process.output


    @staticmethod
    def test_application_start():
        """Will the application start successfully by running the start
        script (runserver.py) directly? Scans the first 100 bytes of stdout to
        ensure logging is propperly being emitted."""

        process = subprocess.Popen(['python', 'runserver.py'],
                    stderr=subprocess.STDOUT,
                    stdout=subprocess.PIPE)

        assert process.pid
        debug_logging = process.stdout.read(100)
        process.kill()
        assert 'Starting application' in debug_logging


if __name__ == '__main__':
    unittest.main()
