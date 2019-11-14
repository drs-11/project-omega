import unittest
import CLIparser

class TestParser(unittest.TestCase):

    def test_basic_usage(self):
        parser = v3.Parser()
        parser.add_argument('key', type=int)
        parser.add_argument('name', type=str)
        self.assertEqual(parser.parse_arguments(["--key=12345", "--name=drs"]), {"key": 12345, "name":"drs"})

    def test_type(self):
        parser = v3.Parser()
        parser.add_argument('key', type=int)
        parser.add_argument('name', type=str)
        with self.assertRaises(v3.WrongTypeError):
            parser.parse_arguments(["--key=cat"])

    def test_missing_arg(self):

        parser = v3.Parser()
        parser.add_argument('key', type=int, required=True)
        parser.add_argument('name', type=str)
        with self.assertRaises(v3.ReqArgError):
            parser.parse_arguments()

    def test_simultaneous_usage(self):
        parser = v3.Parser()
        parser.add_argument('local', type=None)
        parser.add_argument('remote', type=None)
        parser.add_mutually_exclusive_args('local', 'remote')
        with self.assertRaises(v3.SimultaneousUsageError):
            parser.parse_arguments(["--remote", "--local"])

if __name__ == '__main__':
    unittest.main()
