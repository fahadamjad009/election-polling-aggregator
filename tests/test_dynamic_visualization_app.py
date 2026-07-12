from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = ROOT_DIR / "app.py"


class DynamicVisualizationAppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app_text = APP_PATH.read_text(
            encoding="utf-8"
        )

    def test_dynamic_visual_structure(self):
        required_fragments = [
            "DYNAMIC TRAJECTORY AND ERROR EXPLORER V3",
            "polling_trajectory.csv",
            "party_error_distribution.csv",
            "px.line(",
            "px.violin(",
            "Polling volume versus absolute error",
            "Interactive polling trajectory explorer",
            "Error distribution and evidence density",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(
                    fragment,
                    self.app_text,
                )

    def test_historical_route_renders_dynamic_visuals(self):
        app = AppTest.from_file(
            str(APP_PATH)
        )

        app.run(timeout=120)

        if app.exception:
            messages = [
                exception.message
                for exception in app.exception
            ]

            self.fail(
                "\n".join(messages)
            )

        navigation = app.button_group[0]

        navigation.set_value(
            "Historical error analysis"
        )

        app.run(timeout=120)

        if app.exception:
            messages = [
                exception.message
                for exception in app.exception
            ]

            self.fail(
                "\n".join(messages)
            )

        markdown_values = [
            element.value
            for element in app.markdown
        ]

        required_headings = [
            "Interactive polling trajectory explorer",
            "Error distribution and evidence density",
        ]

        for heading in required_headings:
            with self.subTest(heading=heading):
                self.assertTrue(
                    any(
                        heading in value
                        for value in markdown_values
                    ),
                    (
                        "Required dynamic heading "
                        f"was not rendered: {heading}"
                    ),
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)