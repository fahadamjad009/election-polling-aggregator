from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "web" / "public" / "data"

CSV_EXPORTS = {
    "country-performance.json": (
        ROOT / "data" / "presentation" / "country_geographic_performance.csv"
    ),
    "election-errors.json": (
        ROOT / "data" / "presentation" / "election_error_heatmap.csv"
    ),
    "polling-trajectory.json": (
        ROOT / "data" / "presentation" / "polling_trajectory.csv"
    ),
    "party-errors.json": (
        ROOT / "data" / "presentation" / "party_error_distribution.csv"
    ),
    "feature-ablation.json": (
        ROOT
        / "data"
        / "model"
        / "ablation"
        / "development_feature_ablation_metrics.csv"
    ),
    "holdout-metrics.json": (
        ROOT
        / "data"
        / "model"
        / "final_holdout"
        / "final_holdout_metrics.csv"
    ),
    "holdout-country-errors.json": (
        ROOT
        / "data"
        / "model"
        / "final_holdout"
        / "final_holdout_country_errors.csv"
    ),
    "holdout-election-results.json": (
        ROOT
        / "data"
        / "model"
        / "final_holdout"
        / "final_holdout_election_results.csv"
    ),
    "scope-audit.json": (
        ROOT / "data" / "reference" / "polling_table_scope_audit.csv"
    ),
    "scope-included.json": (
        ROOT / "data" / "features" / "polling_scope_included_tables.csv"
    ),
    "scope-excluded.json": (
        ROOT / "data" / "features" / "polling_scope_excluded_tables.csv"
    ),
    "model-dataset-audit.json": (
        ROOT / "data" / "model" / "model_dataset_audit.csv"
    ),
}

MODEL_SELECTION_SOURCE = (
    ROOT
    / "data"
    / "model"
    / "final_holdout"
    / "model_selection_decision.json"
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {}

    for output_name, source_path in CSV_EXPORTS.items():
        if not source_path.exists():
            raise FileNotFoundError(source_path)

        frame = pd.read_csv(source_path)
        output_path = OUTPUT_DIR / output_name

        output_path.write_text(
            frame.to_json(
                orient="records",
                indent=2,
            ),
            encoding="utf-8",
        )

        manifest[output_name] = {
            "source": str(source_path.relative_to(ROOT)).replace("\\", "/"),
            "rows": len(frame),
            "columns": list(frame.columns),
        }

        print(f"{output_name}: {len(frame):,} rows")

    model_selection = json.loads(
        MODEL_SELECTION_SOURCE.read_text(encoding="utf-8")
    )

    (OUTPUT_DIR / "model-selection.json").write_text(
        json.dumps(model_selection, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest["model-selection.json"] = {
        "source": str(
            MODEL_SELECTION_SOURCE.relative_to(ROOT)
        ).replace("\\", "/"),
        "rows": 1,
        "columns": list(model_selection.keys()),
    }

    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    print("React data export: PASS")


if __name__ == "__main__":
    main()

