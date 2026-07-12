import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

FULL_PATH = ROOT / "data/model/model_dataset.csv"
DEV_PATH = ROOT / "data/model/development_model_dataset.csv"
HOLDOUT_PATH = ROOT / "data/model/holdout_model_dataset.csv"
LOCK_PATH = ROOT / "data/model/final_holdout/HOLDOUT_EVALUATED.lock"


class TestModelDataInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full = pd.read_csv(FULL_PATH)
        cls.dev = pd.read_csv(DEV_PATH)
        cls.holdout = pd.read_csv(HOLDOUT_PATH)

    def test_expected_row_counts(self):
        self.assertEqual(len(self.full), 68)
        self.assertEqual(len(self.dev), 43)
        self.assertEqual(len(self.holdout), 25)

    def test_expected_election_counts(self):
        self.assertEqual(
            self.full[["country", "election_year"]]
            .drop_duplicates()
            .shape[0],
            22,
        )
        self.assertEqual(
            self.dev[["country", "election_year"]]
            .drop_duplicates()
            .shape[0],
            14,
        )
        self.assertEqual(
            self.holdout[["country", "election_year"]]
            .drop_duplicates()
            .shape[0],
            8,
        )

    def test_no_duplicate_party_election_rows(self):
        duplicates = self.full.duplicated(
            subset=["country", "election_year", "party"]
        )
        self.assertFalse(duplicates.any())

    def test_one_actual_winner_per_election(self):
        winners = (
            self.full.groupby(["country", "election_year"])["is_winner"]
            .sum()
        )
        self.assertTrue((winners == 1).all())

    def test_development_holdout_do_not_overlap(self):
        dev_elections = set(
            self.dev[["country", "election_year"]]
            .itertuples(index=False, name=None)
        )
        holdout_elections = set(
            self.holdout[["country", "election_year"]]
            .itertuples(index=False, name=None)
        )
        self.assertTrue(dev_elections.isdisjoint(holdout_elections))

    def test_split_labels_are_correct(self):
        self.assertEqual(set(self.dev["dataset_split"]), {"development"})
        self.assertEqual(set(self.holdout["dataset_split"]), {"holdout"})

    def test_required_prediction_fields_are_complete(self):
        required = [
            "country",
            "election_year",
            "party",
            "actual_pct",
            "is_winner",
            "final_rolling_avg",
            "election_date",
            "last_poll_date",
        ]
        self.assertFalse(self.full[required].isna().any().any())

    def test_last_poll_is_not_after_election(self):
        election_date = pd.to_datetime(self.full["election_date"])
        last_poll_date = pd.to_datetime(self.full["last_poll_date"])
        self.assertTrue((last_poll_date <= election_date).all())

    def test_australia_uses_tpp_labels(self):
        australia = self.full[self.full["country"] == "australia"]
        self.assertEqual(
            set(australia["party"]),
            {"ALP (2PP)", "L/NP (2PP)"},
        )

    def test_holdout_lock_exists(self):
        self.assertTrue(LOCK_PATH.exists())
        text = LOCK_PATH.read_text(encoding="utf-8")
        self.assertIn("Do not retune", text)


if __name__ == "__main__":
    unittest.main()
