"""Unit tests for command-line interface execution."""
import unittest
from t900_c900.cli import main


class TestCLI(unittest.TestCase):
    def test_cli_probe_simulation(self):
        code = main(["--simulate", "--profile", "c900-ultra", "probe"])
        self.assertEqual(code, 0)

    def test_cli_probe_json(self):
        code = main(["--simulate", "--profile", "c900-ultra", "--json", "probe", "--qualify"])
        self.assertEqual(code, 0)

    def test_cli_status_simulation(self):
        code = main(["--simulate", "--profile", "c900-ultra", "status"])
        self.assertEqual(code, 0)

    def test_cli_time_sync_simulation(self):
        code = main(["--simulate", "--profile", "c900-ultra", "--dry-run", "time-sync"])
        self.assertEqual(code, 0)

    def test_cli_notify_simulation(self):
        code = main([
            "--simulate",
            "--profile",
            "c900-ultra",
            "--dry-run",
            "notify",
            "--title",
            "Test",
            "--message",
            "CLI Msg",
        ])
        self.assertEqual(code, 0)

    def test_cli_push_dial_simulation(self):
        code = main(["--simulate", "--profile", "c900-ultra", "--dry-run", "push-dial"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
