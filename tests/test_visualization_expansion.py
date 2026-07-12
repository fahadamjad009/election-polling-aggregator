from pathlib import Path
import unittest

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

ABLATION_PATH = (
    ROOT_DIR
    / "data"
    / "model"
    / "ablation"
    / "development_feature_ablation_metrics.csv"
)

SCOPE_PATH = (
    ROOT_DIR
    / "data"
    / "reference"
    / "polling_table_scope_audit.csv"
)

APP_PATH = ROOT_DIR / "app.py"


class VisualizationExpansionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ablation = pd.read_csv(ABLATION_PATH)
        cls.scope = pd.read_csv(SCOPE_PATH)

        cls.app_text = APP_PATH.read_text(
            encoding="utf-8"
        )

    def test_ablation_metric_domain(self):
        self.assertEqual(
            set(self.ablation["metric"]),
            {
                "MAE",
                "RMSE",
                "OOF_ROC_AUC",
                "election_winner_accuracy",
                "row_accuracy_at_0.5",
            },
        )

        self.assertEqual(
            set(self.ablation["feature_set"]),
            {
                "benchmark",
                "final_plus_recent",
                "legacy_broad",
                "recent_compact",
            },
        )

        self.assertEqual(
            set(self.ablation["model"]),
            {
                "final_polling_average",
                "ridge_regression",
                "logistic_regression",
            },
        )

    def test_ablation_values_are_valid(self):
        values = pd.to_numeric(
            self.ablation["value"],
            errors="raise",
        )

        self.assertTrue(
            values.notna().all()
        )

        bounded_metrics = self.ablation.loc[
            self.ablation["metric"].isin(
                {
                    "OOF_ROC_AUC",
                    "election_winner_accuracy",
                    "row_accuracy_at_0.5",
                }
            ),
            "value",
        ]

        self.assertTrue(
            bounded_metrics.between(
                0,
                1,
            ).all()
        )

    def test_scope_audit_totals(self):
        self.assertEqual(
            len(self.scope),
            218,
        )

        self.assertEqual(
            set(self.scope["scope_status"]),
            {
                "review",
                "approved_marker_match",
                "rejected_marker_mismatch",
            },
        )

        self.assertEqual(
            int(self.scope["poll_party_rows"].sum()),
            64216,
        )

        self.assertEqual(
            int(self.scope["country"].nunique()),
            4,
        )

    def test_scope_rows_are_non_negative(self):
        poll_party_rows = pd.to_numeric(
            self.scope["poll_party_rows"],
            errors="raise",
        )

        self.assertTrue(
            (
                poll_party_rows >= 0
            ).all()
        )

    def test_new_visual_sections_exist(self):
        required_fragments = [
            "FEATURE ABLATION HEATMAP V2",
            "SCOPE DONUT AND TREEMAP V2",
            "go.Heatmap(",
            "px.pie(",
            "px.treemap(",
            "Feature-ablation performance matrix",
            "Polling-scope composition",
            "Scope hierarchy by country and source table",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(
                    fragment,
                    self.app_text,
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)