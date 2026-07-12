from pathlib import Path
import unittest

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
PRESENTATION_DIR = ROOT_DIR / "data" / "presentation"

TRAJECTORY_PATH = (
    PRESENTATION_DIR
    / "polling_trajectory.csv"
)

ERROR_PATH = (
    PRESENTATION_DIR
    / "party_error_distribution.csv"
)


class DynamicVisualizationArtifactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trajectory = pd.read_csv(
            TRAJECTORY_PATH
        )

        cls.errors = pd.read_csv(
            ERROR_PATH
        )

    def test_polling_trajectory_shape(self):
        self.assertEqual(
            len(self.trajectory),
            16125,
        )

        election_count = self.trajectory[
            [
                "country",
                "election_year",
            ]
        ].drop_duplicates().shape[0]

        self.assertEqual(
            election_count,
            22,
        )

        self.assertEqual(
            self.trajectory["country"].nunique(),
            4,
        )

    def test_polling_trajectory_dates(self):
        parsed_dates = pd.to_datetime(
            self.trajectory["poll_date"],
            errors="coerce",
        )

        self.assertTrue(
            parsed_dates.notna().all()
        )

    def test_polling_trajectory_values(self):
        self.assertTrue(
            self.trajectory["pct"].notna().all()
        )

        self.assertTrue(
            self.trajectory[
                "rolling_avg"
            ].notna().all()
        )

        self.assertGreater(
            int(
                self.trajectory[
                    "model_included"
                ].sum()
            ),
            0,
        )

    def test_party_error_shape(self):
        self.assertEqual(
            len(self.errors),
            68,
        )

        split_counts = (
            self.errors[
                "evaluation_split"
            ]
            .value_counts()
            .to_dict()
        )

        self.assertEqual(
            split_counts,
            {
                "Development": 43,
                "Holdout": 25,
            },
        )

    def test_party_error_uniqueness(self):
        duplicate_count = int(
            self.errors[
                [
                    "country",
                    "election_year",
                    "party",
                ]
            ].duplicated().sum()
        )

        self.assertEqual(
            duplicate_count,
            0,
        )

    def test_party_error_consistency(self):
        difference = (
            self.errors[
                "signed_error"
            ].abs()
            - self.errors[
                "absolute_error"
            ]
        ).abs()

        self.assertLessEqual(
            float(difference.max()),
            1e-6,
        )

        self.assertTrue(
            (
                self.errors[
                    "absolute_error"
                ]
                >= 0
            ).all()
        )

    def test_polling_volume_is_available(self):
        self.assertTrue(
            (
                self.errors[
                    "n_poll_observations"
                ]
                > 0
            ).all()
        )

        self.assertTrue(
            (
                self.errors[
                    "bubble_size"
                ]
                > 0
            ).all()
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)