from pathlib import Path
import unittest

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
PRESENTATION_DIR = ROOT_DIR / "data" / "presentation"

COUNTRY_PATH = (
    PRESENTATION_DIR
    / "country_geographic_performance.csv"
)

ELECTION_PATH = (
    PRESENTATION_DIR
    / "election_error_heatmap.csv"
)


class VisualizationArtifactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.countries = pd.read_csv(COUNTRY_PATH)
        cls.elections = pd.read_csv(ELECTION_PATH)

    def test_expected_country_coverage(self):
        self.assertEqual(
            set(self.countries["iso_alpha"]),
            {
                "AUS",
                "CAN",
                "GBR",
                "USA",
            },
        )

        self.assertEqual(
            len(self.countries),
            4,
        )

    def test_expected_election_coverage(self):
        self.assertEqual(
            len(self.elections),
            22,
        )

        duplicate_count = int(
            self.elections[
                [
                    "country",
                    "election_year",
                ]
            ].duplicated().sum()
        )

        self.assertEqual(
            duplicate_count,
            0,
        )

    def test_errors_are_non_negative(self):
        self.assertTrue(
            (
                self.countries["mean_absolute_error"]
                >= 0
            ).all()
        )

        self.assertTrue(
            (
                self.elections["election_mae"]
                >= 0
            ).all()
        )

    def test_winner_totals_are_consistent(self):
        self.assertEqual(
            int(self.countries["elections"].sum()),
            22,
        )

        self.assertEqual(
            int(self.countries["wrong_winners"].sum()),
            2,
        )

        calculated_accuracy = (
            self.countries["correct_winners"]
            / self.countries["elections"]
        )

        pd.testing.assert_series_equal(
            calculated_accuracy.reset_index(drop=True),
            self.countries[
                "winner_accuracy"
            ].reset_index(drop=True),
            check_names=False,
            rtol=1e-6,
            atol=1e-6,
        )

    def test_known_winner_misses_are_preserved(self):
        misses = self.elections.loc[
            self.elections["winner_correct"] == 0,
            [
                "country",
                "election_year",
            ],
        ]

        actual_misses = {
            (
                row.country,
                int(row.election_year),
            )
            for row in misses.itertuples(
                index=False
            )
        }

        self.assertEqual(
            actual_misses,
            {
                ("australia", 2019),
                ("us", 2000),
            },
        )

    def test_map_bubble_measure_is_available(self):
        self.assertTrue(
            (
                self.countries["poll_observations"]
                > 0
            ).all()
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)