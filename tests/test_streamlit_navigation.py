from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = ROOT_DIR / "app.py"

SECTION_HEADINGS = {
    "Overview": "Project evidence summary",
    "Development validation": (
        "Development validation and model selection"
    ),
    "Historical error analysis": (
        "Historical polling-error analysis"
    ),
    "Polling-scope audit": (
        "National polling-scope audit"
    ),
    "Chronological holdout": (
        "Interactive chronological holdout explorer"
    ),
    "Australia 2019 case study": (
        "Australia 2019: honest failure analysis"
    ),
    "Methodology and governance": (
        "Model-selection decision"
    ),
}


class StreamlitNavigationTest(unittest.TestCase):
    def create_app(self):
        app = AppTest.from_file(str(APP_PATH))
        app.run(timeout=120)
        return app

    def assert_no_app_exceptions(self, app):
        messages = [
            exception.message
            for exception in app.exception
        ]

        self.assertEqual(
            messages,
            [],
            "\n".join(messages),
        )

    def test_default_navigation_state(self):
        app = self.create_app()

        self.assert_no_app_exceptions(app)

        self.assertEqual(
            len(app.button_group),
            1,
            "Expected exactly one pill-navigation widget.",
        )

        self.assertEqual(
            len(app.tabs),
            0,
            "Legacy st.tabs elements must not be rendered.",
        )

        headings = [
            heading.value
            for heading in app.subheader
        ]

        self.assertIn(
            SECTION_HEADINGS["Overview"],
            headings,
        )

    def test_every_navigation_section_renders(self):
        app = self.create_app()

        self.assert_no_app_exceptions(app)

        for section, expected_heading in SECTION_HEADINGS.items():
            with self.subTest(section=section):
                navigation = app.button_group[0]
                navigation.set_value(section)

                app.run(timeout=120)

                self.assert_no_app_exceptions(app)

                self.assertEqual(
                    len(app.button_group),
                    1,
                    "Pill navigation disappeared after rerun.",
                )

                self.assertEqual(
                    len(app.tabs),
                    0,
                    "Legacy tabs reappeared after navigation.",
                )

                headings = [
                    heading.value
                    for heading in app.subheader
                ]

                self.assertIn(
                    expected_heading,
                    headings,
                    (
                        f"Expected heading not rendered for "
                        f"section: {section}"
                    ),
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)