import unittest
from ..settings import Configuration

# python -m unittest discover -s ./snowypushy/tests -t ..
class TestConfiguration(unittest.TestCase):
    def test_config(self):
        config = Configuration("examples/sample.yml")
        self.assertIsInstance(config, Configuration)
        self.assertEqual(None, config.get("A"))
        self.assertEqual("REPLACE", config.get("UPDATE_METHOD"))
