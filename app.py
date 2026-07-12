import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
CSS_PATH = ROOT_DIR / "assets" / "app.css"
REFERENCE_DIR = ROOT_DIR / "data" / "reference"
MODEL_DIR = ROOT_DIR / "data" / "model"
BASELINE_DIR = MODEL_DIR / "baselines"
ABLATION_DIR = MODEL_DIR / "ablation"
HOLDOUT_DIR = MODEL_DIR / "final_holdout"
PRESENTATION_DIR = ROOT_DIR / "data" / "presentation"

ARTIFACT_PATHS = {
    "model_dataset": MODEL_DIR / "model_dataset.csv",
    "model_audit": MODEL_DIR / "model_dataset_audit.csv",
    "scope_audit": (
        REFERENCE_DIR / "polling_table_scope_audit.csv"
    ),
    "development_metrics": (
        BASELINE_DIR / "development_baseline_metrics.csv"
    ),
    "development_elections": (
        BASELINE_DIR / "development_election_predictions.csv"
    ),
    "development_country_errors": (
        BASELINE_DIR / "development_error_by_country.csv"
    ),
    "development_party_errors": (
        BASELINE_DIR / "development_party_error_detail.csv"
    ),
    "development_election_errors": (
        BASELINE_DIR / "development_error_by_election.csv"
    ),
    "ablation_metrics": (
        ABLATION_DIR / "development_feature_ablation_metrics.csv"
    ),
    "holdout_metrics": HOLDOUT_DIR / "final_holdout_metrics.csv",
    "holdout_predictions": HOLDOUT_DIR / "final_holdout_predictions.csv",
    "holdout_elections": HOLDOUT_DIR / "final_holdout_election_results.csv",
    "holdout_country_errors": HOLDOUT_DIR / "final_holdout_country_errors.csv",
    "selection_decision": HOLDOUT_DIR / "model_selection_decision.json",
    "holdout_lock": HOLDOUT_DIR / "HOLDOUT_EVALUATED.lock",
    "country_geographic_performance": (
        PRESENTATION_DIR / "country_geographic_performance.csv"
    ),
    "election_error_heatmap": (
        PRESENTATION_DIR / "election_error_heatmap.csv"
    ),
    "polling_trajectory": (
        PRESENTATION_DIR / "polling_trajectory.csv"
    ),
    "party_error_distribution": (
        PRESENTATION_DIR / "party_error_distribution.csv"
    ),
}


st.set_page_config(
    page_title="Election Polling Aggregator",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if CSS_PATH.exists():
    st.markdown(
        f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


@st.cache_data
def load_artifacts():
    missing = [
        str(path.relative_to(ROOT_DIR))
        for path in ARTIFACT_PATHS.values()
        if not path.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Missing application artifacts: " + ", ".join(missing)
        )

    with ARTIFACT_PATHS["selection_decision"].open(
        "r",
        encoding="utf-8",
    ) as file:
        selection_decision = json.load(file)

    holdout_lock = ARTIFACT_PATHS["holdout_lock"].read_text(
        encoding="utf-8",
    ).strip()

    return {
        "model_dataset": pd.read_csv(
            ARTIFACT_PATHS["model_dataset"]
        ),
        "model_audit": pd.read_csv(
            ARTIFACT_PATHS["model_audit"]
        ),
        "scope_audit": pd.read_csv(
            ARTIFACT_PATHS["scope_audit"]
        ),
        "development_metrics": pd.read_csv(
            ARTIFACT_PATHS["development_metrics"]
        ),
        "development_elections": pd.read_csv(
            ARTIFACT_PATHS["development_elections"]
        ),
        "development_country_errors": pd.read_csv(
            ARTIFACT_PATHS["development_country_errors"]
        ),
        "development_party_errors": pd.read_csv(
            ARTIFACT_PATHS["development_party_errors"]
        ),
        "development_election_errors": pd.read_csv(
            ARTIFACT_PATHS["development_election_errors"]
        ),
        "ablation_metrics": pd.read_csv(
            ARTIFACT_PATHS["ablation_metrics"]
        ),
        "holdout_metrics": pd.read_csv(
            ARTIFACT_PATHS["holdout_metrics"]
        ),
        "holdout_predictions": pd.read_csv(
            ARTIFACT_PATHS["holdout_predictions"]
        ),
        "holdout_elections": pd.read_csv(
            ARTIFACT_PATHS["holdout_elections"]
        ),
        "holdout_country_errors": pd.read_csv(
            ARTIFACT_PATHS["holdout_country_errors"]
        ),
        "selection_decision": selection_decision,
        "holdout_lock": holdout_lock,
        "country_geographic_performance": pd.read_csv(
            ARTIFACT_PATHS["country_geographic_performance"]
        ),
        "election_error_heatmap": pd.read_csv(
            ARTIFACT_PATHS["election_error_heatmap"]
        ),
        "polling_trajectory": pd.read_csv(
            ARTIFACT_PATHS["polling_trajectory"]
        ),
        "party_error_distribution": pd.read_csv(
            ARTIFACT_PATHS["party_error_distribution"]
        ),
    }


def metric_value(metrics, metric_name):
    match = metrics.loc[
        metrics["metric"].str.upper() == metric_name.upper(),
        "value",
    ]

    if match.empty:
        raise ValueError(
            f"Metric not found in holdout artifact: {metric_name}"
        )

    return float(match.iloc[0])


def csv_bytes(dataframe):
    return dataframe.to_csv(index=False).encode("utf-8")


def style_figure(figure, title, height=430):
    figure.update_layout(
        title={
            "text": title,
            "x": 0.02,
            "xanchor": "left",
        },
        height=height,
        margin={
            "l": 25,
            "r": 25,
            "t": 75,
            "b": 25,
        },
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        font={
            "color": "#E8EEF7",
        },
        legend_title_text="",
        hoverlabel={
            "namelength": -1,
        },
    )

    figure.update_xaxes(
        gridcolor="rgba(148, 163, 184, 0.15)",
        zerolinecolor="rgba(148, 163, 184, 0.30)",
    )

    figure.update_yaxes(
        gridcolor="rgba(148, 163, 184, 0.15)",
        zerolinecolor="rgba(148, 163, 184, 0.30)",
    )

    return figure


try:
    artifacts = load_artifacts()
except (FileNotFoundError, ValueError, KeyError) as error:
    st.error(f"Application artifact loading failed: {error}")
    st.stop()


model_dataset = artifacts["model_dataset"]
model_audit = artifacts["model_audit"]
scope_audit = artifacts["scope_audit"]
development_metrics = artifacts["development_metrics"]
development_elections = artifacts["development_elections"]
development_country_errors = artifacts["development_country_errors"]
development_party_errors = artifacts["development_party_errors"]
development_election_errors = artifacts["development_election_errors"]
ablation_metrics = artifacts["ablation_metrics"]
holdout_metrics = artifacts["holdout_metrics"]
holdout_predictions = artifacts["holdout_predictions"]
holdout_elections = artifacts["holdout_elections"]
holdout_country_errors = artifacts["holdout_country_errors"]
selection_decision = artifacts["selection_decision"]
holdout_lock = artifacts["holdout_lock"]
country_geographic_performance = artifacts[
    "country_geographic_performance"
]
election_error_heatmap = artifacts[
    "election_error_heatmap"
]
polling_trajectory = artifacts[
    "polling_trajectory"
]
party_error_distribution = artifacts[
    "party_error_distribution"
]

total_elections = int(len(model_audit))
total_countries = int(model_audit["country"].nunique())
total_party_rows = int(len(model_dataset))

development_election_count = int(
    (
        model_audit["dataset_split"] == "development"
    ).sum()
)

holdout_election_count = int(
    (
        model_audit["dataset_split"] == "holdout"
    ).sum()
)

holdout_mae = metric_value(
    holdout_metrics,
    "MAE",
)

holdout_rmse = metric_value(
    holdout_metrics,
    "RMSE",
)

holdout_winner_accuracy = float(
    holdout_elections["winner_correct"].mean()
)

correct_holdout_winners = int(
    holdout_elections["winner_correct"].sum()
)

selected_model = str(
    selection_decision["selected_model"]
)

development_mae = float(
    selection_decision["development_mae"]
)

development_winner_accuracy = float(
    selection_decision["development_winner_accuracy"]
)


st.title("Election Polling Aggregator")

st.caption(
    "Historical national polling analysis with election-level validation, "
    "a frozen chronological holdout, and explicitly documented limitations."
)


governance_status = holdout_lock.splitlines()[0]

st.html(
    f"""
    <section class="governance-strip">
        <div class="governance-cell">
            <span class="governance-eyebrow">
                Evaluation governance
            </span>
            <strong class="governance-status">
                {governance_status}
            </strong>
            <span class="governance-description">
                Frozen outputs only. No model fitting, tuning,
                or holdout reselection occurs in this application.
            </span>
        </div>

        <div class="governance-cell">
            <span class="governance-label">
                Development elections
            </span>
            <strong class="governance-value">
                {development_election_count}
            </strong>
        </div>

        <div class="governance-cell">
            <span class="governance-label">
                Holdout elections
            </span>
            <strong class="governance-value">
                {holdout_election_count}
            </strong>
        </div>

        <div class="governance-cell">
            <span class="governance-label">
                Selected method
            </span>
            <strong class="governance-method">
                {selected_model}
            </strong>
        </div>
    </section>
    """
)

NAVIGATION_OPTIONS = [
    "Overview",
    "Development validation",
    "Historical error analysis",
    "Polling-scope audit",
    "Chronological holdout",
    "Australia 2019 case study",
    "Methodology and governance",
]

selected_section = st.pills(
    "Dashboard section",
    NAVIGATION_OPTIONS,
    selection_mode="single",
    default="Overview",
    required=True,
    key="dashboard_section_navigation",
    label_visibility="collapsed",
    width="stretch",
)


if selected_section == "Overview":
    st.subheader("Project evidence summary")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Countries",
        total_countries,
    )

    c2.metric(
        "Elections",
        total_elections,
    )

    c3.metric(
        "Party-election rows",
        total_party_rows,
    )

    c4.metric(
        "Holdout MAE",
        f"{holdout_mae:.2f} pp",
    )

    c5.metric(
        "Holdout winners",
        f"{correct_holdout_winners}/{holdout_election_count}",
    )

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.markdown("### Development validation")

            st.metric(
                "Leave-one-election-out MAE",
                f"{development_mae:.2f} pp",
            )

            st.metric(
                "Election-winner accuracy",
                f"{development_winner_accuracy:.1%}",
            )

            st.markdown(
                selection_decision["selection_basis"]
            )

    with right:
        with st.container(border=True):
            st.markdown("### Frozen holdout")

            st.metric(
                "Vote-share RMSE",
                f"{holdout_rmse:.2f} pp",
            )

            st.metric(
                "Election-winner accuracy",
                f"{holdout_winner_accuracy:.1%}",
            )

            st.markdown(
                selection_decision["holdout_usage"]
            )

    st.markdown("### Dataset split")

    split_summary = (
        model_audit.groupby(
            ["dataset_split", "country"],
            as_index=False,
        )
        .agg(
            elections=("election_year", "count"),
            model_party_rows=("model_party_rows", "sum"),
            source_feature_rows=("source_feature_rows", "sum"),
        )
        .sort_values(
            ["dataset_split", "country"]
        )
    )

    st.dataframe(
        split_summary,
        width="stretch",
        hide_index=True,
    )



    # GEOGRAPHIC PERFORMANCE MAP V1
    st.markdown(
        "### Geographic coverage and historical polling error"
    )

    st.caption(
        "Country-level evidence only. Bubble size represents the "
        "number of poll observations feeding the model dataset; "
        "colour represents weighted party-level mean absolute "
        "error. This does not imply state, province, district or "
        "constituency-level hotspot evidence."
    )

    map_view = country_geographic_performance.copy()

    map_view["winner_record"] = (
        map_view["correct_winners"].astype(int).astype(str)
        + " correct / "
        + map_view["elections"].astype(int).astype(str)
        + " elections"
    )

    map_view["miss_record"] = map_view[
        "wrong_winners"
    ].astype(int).map(
        lambda value: (
            "No winner misses"
            if value == 0
            else f"{value} winner miss"
        )
    )

    geographic_figure = px.scatter_geo(
        map_view,
        locations="iso_alpha",
        locationmode="ISO-3",
        size="poll_observations",
        color="mean_absolute_error",
        hover_name="country_label",
        hover_data={
            "iso_alpha": False,
            "poll_observations": ":,",
            "campaign_party_rows": ":,",
            "evaluated_party_rows": ":,",
            "elections": ":.0f",
            "winner_record": True,
            "miss_record": True,
            "winner_accuracy_pct": ":.1f",
            "mean_absolute_error": ":.2f",
            "median_absolute_error": ":.2f",
            "maximum_absolute_error": ":.2f",
            "worst_election": True,
            "worst_election_mae": ":.2f",
            "worst_election_result_status": True,
        },
        labels={
            "poll_observations": "Poll observations",
            "campaign_party_rows": "Model party rows",
            "evaluated_party_rows": "Evaluated party rows",
            "elections": "Elections",
            "winner_record": "Winner record",
            "miss_record": "Historical misses",
            "winner_accuracy_pct": "Winner accuracy (%)",
            "mean_absolute_error": "Mean absolute error (pp)",
            "median_absolute_error": "Median absolute error (pp)",
            "maximum_absolute_error": "Maximum absolute error (pp)",
            "worst_election": "Highest-MAE election",
            "worst_election_mae": "Highest election MAE (pp)",
            "worst_election_result_status": "Highest-MAE result",
        },
        projection="natural earth",
        color_continuous_scale="Plasma",
        size_max=58,
    )

    geographic_figure.update_traces(
        marker={
            "line": {
                "color": "rgba(235, 241, 250, 0.85)",
                "width": 1.2,
            },
            "opacity": 0.88,
        }
    )

    geographic_figure.update_geos(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="rgba(148, 163, 184, 0.42)",
        showcountries=True,
        countrycolor="rgba(148, 163, 184, 0.28)",
        showland=True,
        landcolor="rgba(20, 35, 55, 0.74)",
        showocean=True,
        oceancolor="rgba(4, 13, 27, 0.46)",
        bgcolor="rgba(0, 0, 0, 0)",
    )

    geographic_figure = style_figure(
        geographic_figure,
        (
            "Cross-country polling coverage and "
            "historical error"
        ),
        height=565,
    )

    geographic_figure.update_layout(
        geo={
            "projection_scale": 1.02,
        },
        coloraxis_colorbar={
            "title": {
                "text": "MAE<br>(pp)",
            },
            "thickness": 14,
        },
        margin={
            "l": 5,
            "r": 5,
            "t": 78,
            "b": 5,
        },
    )

    st.plotly_chart(
        geographic_figure,
        width="stretch",
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
        key="country_geographic_performance_map",
    )

    map_download_col, map_note_col = st.columns(
        [
            0.28,
            0.72,
        ]
    )

    with map_download_col:
        st.download_button(
            "Download geographic map data",
            data=csv_bytes(
                country_geographic_performance
            ),
            file_name=(
                "country_geographic_performance.csv"
            ),
            mime="text/csv",
            key="download_country_geographic_performance",
        )

    with map_note_col:
        st.info(
            "The map summarises national-level evaluation. "
            "Regional boundaries are intentionally not coloured "
            "because comparable subnational polling-error data "
            "is not available across all four countries."
        )

    st.markdown("### Election-level error matrix")

    st.caption(
        "Each populated cell represents one frozen development or "
        "holdout election. Colour shows election MAE in percentage "
        "points. The annotation records the MAE and whether the "
        "polling-average method selected the correct winner."
    )

    heatmap_view = election_error_heatmap.copy()

    heatmap_view["winner_correct"] = pd.to_numeric(
        heatmap_view["winner_correct"],
        errors="raise",
    ).astype(int)

    country_order = [
        "Australia",
        "Canada",
        "United Kingdom",
        "United States",
    ]

    election_years = sorted(
        heatmap_view["election_year"]
        .astype(int)
        .unique()
        .tolist()
    )

    heatmap_z = []
    heatmap_text = []
    heatmap_custom = []

    for country_label in country_order:
        country_values = heatmap_view.loc[
            heatmap_view["country_label"] == country_label
        ].set_index("election_year")

        z_row = []
        text_row = []
        custom_row = []

        for election_year in election_years:
            if election_year not in country_values.index:
                z_row.append(None)
                text_row.append("")
                custom_row.append(
                    [
                        country_label,
                        election_year,
                        "",
                        "",
                        "",
                        "",
                    ]
                )
                continue

            election_row = country_values.loc[
                election_year
            ]

            election_mae = float(
                election_row["election_mae"]
            )

            winner_correct = int(
                election_row["winner_correct"]
            )

            status_text = (
                "Correct winner"
                if winner_correct == 1
                else "Winner miss"
            )

            z_row.append(election_mae)

            text_row.append(
                f"{election_mae:.2f}<br>"
                + (
                    "OK"
                    if winner_correct == 1
                    else "MISS"
                )
            )

            custom_row.append(
                [
                    country_label,
                    election_year,
                    election_row["split"],
                    election_row["actual_winner"],
                    election_row["predicted_winner"],
                    status_text,
                ]
            )

        heatmap_z.append(z_row)
        heatmap_text.append(text_row)
        heatmap_custom.append(custom_row)

    maximum_heatmap_error = max(
        3.0,
        float(
            heatmap_view["election_mae"].max()
        ),
    )

    heatmap_figure = go.Figure(
        data=go.Heatmap(
            z=heatmap_z,
            x=election_years,
            y=country_order,
            text=heatmap_text,
            customdata=heatmap_custom,
            texttemplate="%{text}",
            textfont={
                "size": 10,
                "color": "#F8FAFC",
            },
            hovertemplate=(
                "<b>%{customdata[0]} "
                "%{customdata[1]}</b><br>"
                "Split: %{customdata[2]}<br>"
                "Election MAE: %{z:.2f} pp<br>"
                "Actual winner: %{customdata[3]}<br>"
                "Predicted winner: %{customdata[4]}<br>"
                "Result: %{customdata[5]}"
                "<extra></extra>"
            ),
            colorscale=[
                [
                    0.0,
                    "#16304D",
                ],
                [
                    0.45,
                    "#3B82B6",
                ],
                [
                    0.72,
                    "#C9A961",
                ],
                [
                    1.0,
                    "#D65D66",
                ],
            ],
            zmin=0,
            zmax=maximum_heatmap_error,
            xgap=3,
            ygap=3,
            colorbar={
                "title": {
                    "text": "MAE<br>(pp)",
                },
                "thickness": 14,
            },
            hoverongaps=False,
        )
    )

    heatmap_figure = style_figure(
        heatmap_figure,
        "Election error and winner-correctness matrix",
        height=430,
    )

    heatmap_figure.update_layout(
        xaxis={
            "title": "Election year",
            "side": "top",
            "tickmode": "array",
            "tickvals": election_years,
            "ticktext": [
                str(year)
                for year in election_years
            ],
            "tickangle": -45,
        },
        yaxis={
            "title": "",
            "autorange": "reversed",
        },
        margin={
            "l": 25,
            "r": 25,
            "t": 105,
            "b": 35,
        },
    )

    st.plotly_chart(
        heatmap_figure,
        width="stretch",
        config={
            "displaylogo": False,
        },
        key="election_error_heatmap",
    )

    heatmap_download_col, heatmap_note_col = st.columns(
        [
            0.28,
            0.72,
        ]
    )

    with heatmap_download_col:
        st.download_button(
            "Download election heatmap data",
            data=csv_bytes(
                election_error_heatmap
            ),
            file_name="election_error_heatmap.csv",
            mime="text/csv",
            key="download_election_error_heatmap",
        )

    with heatmap_note_col:
        st.caption(
            "MISS identifies the two retained historical "
            "winner-selection failures: United States 2000 and "
            "Australia 2019. These cases are not hidden or "
            "removed from the presentation."
        )


elif selected_section == "Development validation":
    st.subheader("Development validation and model selection")

    st.caption(
        "All results in this section come from development elections. "
        "The chronological holdout was not used to select the final method."
    )

    benchmark_mae = float(
        selection_decision["development_mae"]
    )

    benchmark_rmse = float(
        selection_decision["development_rmse"]
    )

    benchmark_accuracy = float(
        selection_decision["development_winner_accuracy"]
    )

    tested_models = int(
        development_metrics["model"].nunique()
    )

    v1, v2, v3, v4 = st.columns(4)

    v1.metric(
        "Development elections",
        development_elections[
            ["country", "election_year"]
        ].drop_duplicates().shape[0],
    )

    v2.metric(
        "Selected-model MAE",
        f"{benchmark_mae:.2f} pp",
    )

    v3.metric(
        "Selected-model RMSE",
        f"{benchmark_rmse:.2f} pp",
    )

    v4.metric(
        "Winner accuracy",
        f"{benchmark_accuracy:.1%}",
    )

    st.info(
        f"{tested_models} candidate modelling approaches were evaluated. "
        "The final polling average remained the selected method because "
        "it produced the strongest development validation performance."
    )

    model_labels = {
        "final_polling_average": "Final polling average",
        "ridge_regression": "Ridge regression",
        "logistic_regression": "Logistic regression",
    }

    metric_view = development_metrics.copy()

    metric_view["model_label"] = (
        metric_view["model"]
        .map(model_labels)
        .fillna(metric_view["model"])
    )

    regression_metrics = metric_view.loc[
        metric_view["metric"].str.upper().isin(
            ["MAE", "RMSE"]
        )
    ].copy()

    winner_metrics = metric_view.loc[
        metric_view["metric"]
        .str.lower()
        .str.contains("winner_accuracy")
    ].copy()

    winner_metrics["accuracy_pct"] = (
        winner_metrics["value"] * 100
    )

    chart_left, chart_right = st.columns(2)

    regression_figure = px.bar(
        regression_metrics,
        x="metric",
        y="value",
        color="model_label",
        barmode="group",
        text_auto=".2f",
        hover_data={
            "task": True,
            "value": ":.3f",
        },
        color_discrete_sequence=[
            "#F2B84B",
            "#4EA1FF",
            "#32C7C9",
        ],
    )

    regression_figure.update_layout(
        xaxis_title="",
        yaxis_title="Error (percentage points)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    with chart_left:
        st.plotly_chart(
            style_figure(
                regression_figure,
                "Development vote-share error",
                height=430,
            ),
            width="stretch",
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

    winner_figure = px.bar(
        winner_metrics,
        x="model_label",
        y="accuracy_pct",
        color="model_label",
        text_auto=".1f",
        hover_data={
            "metric": False,
            "value": ":.3f",
        },
        color_discrete_sequence=[
            "#F2B84B",
            "#4EA1FF",
            "#32C7C9",
        ],
    )

    winner_figure.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="Election-winner accuracy (%)",
        yaxis_range=[0, 105],
    )

    with chart_right:
        st.plotly_chart(
            style_figure(
                winner_figure,
                "Development winner accuracy",
                height=430,
            ),
            width="stretch",
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

    st.markdown("### Country-level validation error")

    country_comparison = development_country_errors[
        [
            "country",
            "baseline_mae",
            "ridge_mae",
        ]
    ].copy()

    country_comparison["country"] = (
        country_comparison["country"].str.title()
    )

    country_comparison = country_comparison.melt(
        id_vars=["country"],
        value_vars=[
            "baseline_mae",
            "ridge_mae",
        ],
        var_name="model",
        value_name="MAE",
    )

    country_comparison["model"] = (
        country_comparison["model"].map(
            {
                "baseline_mae": "Final polling average",
                "ridge_mae": "Ridge regression",
            }
        )
    )

    country_figure = px.bar(
        country_comparison,
        x="country",
        y="MAE",
        color="model",
        barmode="group",
        text_auto=".2f",
        color_discrete_map={
            "Final polling average": "#F2B84B",
            "Ridge regression": "#4EA1FF",
        },
    )

    country_figure.update_layout(
        xaxis_title="",
        yaxis_title="Mean absolute error (pp)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    st.plotly_chart(
        style_figure(
            country_figure,
            "Final polling average versus Ridge by country",
            height=450,
        ),
        width="stretch",
        config={
            "displaylogo": False,
            "responsive": True,
        },
    )

    st.markdown("### Feature-ablation evidence")

    available_ablation_metrics = sorted(
        ablation_metrics["metric"]
        .dropna()
        .unique()
        .tolist()
    )

    default_ablation_index = (
        available_ablation_metrics.index("MAE")
        if "MAE" in available_ablation_metrics
        else 0
    )

    selected_ablation_metric = st.selectbox(
        "Ablation metric",
        available_ablation_metrics,
        index=default_ablation_index,
        format_func=lambda value: (
            value.replace("_", " ").title()
        ),
        key="ablation_metric",
    )

    ablation_view = ablation_metrics.loc[
        ablation_metrics["metric"]
        == selected_ablation_metric
    ].copy()

    ablation_view["model_label"] = (
        ablation_view["model"]
        .map(model_labels)
        .fillna(ablation_view["model"])
    )

    ablation_view["feature_label"] = (
        ablation_view["feature_set"]
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    ablation_plot_value = "value"
    ablation_axis_title = selected_ablation_metric.replace(
        "_",
        " ",
    ).title()

    if "accuracy" in selected_ablation_metric.lower():
        ablation_view["display_value"] = (
            ablation_view["value"] * 100
        )

        ablation_plot_value = "display_value"
        ablation_axis_title += " (%)"

    ablation_figure = px.bar(
        ablation_view,
        x="feature_label",
        y=ablation_plot_value,
        color="model_label",
        barmode="group",
        text_auto=".2f",
        hover_data={
            "feature_set": False,
            "value": ":.4f",
        },
        color_discrete_sequence=[
            "#F2B84B",
            "#4EA1FF",
            "#32C7C9",
            "#A78BFA",
        ],
    )

    ablation_figure.update_layout(
        xaxis_title="Feature configuration",
        yaxis_title=ablation_axis_title,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    st.plotly_chart(
        style_figure(
            ablation_figure,
            (
                "Feature-ablation comparison: "
                f"{ablation_axis_title}"
            ),
            height=470,
        ),
        width="stretch",
        config={
            "displaylogo": False,
            "responsive": True,
        },
    )

    detail_left, detail_right = st.columns(2)

    with detail_left:
        st.markdown("### Election-level validation")

        election_detail = development_elections.copy()

        election_detail["country"] = (
            election_detail["country"].str.title()
        )

        election_detail["Polling average"] = (
            election_detail["polling_baseline_correct"]
            .astype(int)
            .map(
                {
                    1: "Correct",
                    0: "Miss",
                }
            )
        )

        election_detail["Ridge"] = (
            election_detail["ridge_correct"]
            .astype(int)
            .map(
                {
                    1: "Correct",
                    0: "Miss",
                }
            )
        )

        election_detail["Logistic"] = (
            election_detail["logistic_correct"]
            .astype(int)
            .map(
                {
                    1: "Correct",
                    0: "Miss",
                }
            )
        )

        election_detail = election_detail[
            [
                "country",
                "election_year",
                "actual_winner",
                "Polling average",
                "Ridge",
                "Logistic",
            ]
        ].rename(
            columns={
                "country": "Country",
                "election_year": "Election",
                "actual_winner": "Actual winner",
            }
        )

        st.dataframe(
            election_detail.sort_values(
                [
                    "Country",
                    "Election",
                ]
            ),
            width="stretch",
            hide_index=True,
            height=420,
        )

    with detail_right:
        st.markdown("### Largest party-level misses")

        largest_errors = (
            development_party_errors
            .nlargest(
                12,
                "baseline_abs_error",
            )
            .copy()
        )

        largest_errors["country"] = (
            largest_errors["country"].str.title()
        )

        largest_errors = largest_errors[
            [
                "country",
                "election_year",
                "party",
                "actual_pct",
                "baseline_vote_prediction",
                "baseline_error",
                "baseline_abs_error",
            ]
        ].rename(
            columns={
                "country": "Country",
                "election_year": "Election",
                "party": "Party",
                "actual_pct": "Actual vote",
                "baseline_vote_prediction": "Polling average",
                "baseline_error": "Signed error",
                "baseline_abs_error": "Absolute error",
            }
        )

        st.dataframe(
            largest_errors,
            width="stretch",
            hide_index=True,
            height=420,
            column_config={
                "Actual vote": st.column_config.NumberColumn(
                    format="%.2f%%",
                ),
                "Polling average": st.column_config.NumberColumn(
                    format="%.2f%%",
                ),
                "Signed error": st.column_config.NumberColumn(
                    format="%.2f pp",
                ),
                "Absolute error": st.column_config.NumberColumn(
                    format="%.2f pp",
                ),
            },
        )



    # FEATURE ABLATION HEATMAP V2
    st.markdown(
        "### Feature-ablation performance matrix"
    )

    st.caption(
        "This matrix complements the existing grouped bar chart. "
        "Empty cells represent model-feature combinations that were "
        "not evaluated rather than zero-valued results."
    )

    ablation_heatmap_labels = {
        "MAE": "Vote-share MAE",
        "RMSE": "Vote-share RMSE",
        "election_winner_accuracy": "Election winner accuracy",
        "OOF_ROC_AUC": "Out-of-fold ROC AUC",
        "row_accuracy_at_0.5": "Row accuracy at 0.5",
    }

    ablation_heatmap_options = [
        metric
        for metric in [
            "MAE",
            "RMSE",
            "election_winner_accuracy",
            "OOF_ROC_AUC",
            "row_accuracy_at_0.5",
        ]
        if metric in set(ablation_metrics["metric"])
    ]

    selected_heatmap_metric = st.selectbox(
        "Ablation heatmap metric",
        options=ablation_heatmap_options,
        format_func=lambda value: (
            ablation_heatmap_labels[value]
        ),
        key="ablation_heatmap_metric",
    )

    ablation_heatmap_view = ablation_metrics.loc[
        ablation_metrics["metric"]
        == selected_heatmap_metric
    ].copy()

    feature_order = [
        "benchmark",
        "final_plus_recent",
        "recent_compact",
        "legacy_broad",
    ]

    model_order = [
        "final_polling_average",
        "ridge_regression",
        "logistic_regression",
    ]

    feature_labels = {
        "benchmark": "Benchmark",
        "final_plus_recent": "Final + recent",
        "recent_compact": "Recent compact",
        "legacy_broad": "Legacy broad",
    }

    heatmap_model_labels = {
        "final_polling_average": "Polling average",
        "ridge_regression": "Ridge regression",
        "logistic_regression": "Logistic regression",
    }

    bounded_heatmap_metric = (
        selected_heatmap_metric
        in {
            "election_winner_accuracy",
            "OOF_ROC_AUC",
            "row_accuracy_at_0.5",
        }
    )

    ablation_heatmap_view["display_value"] = pd.to_numeric(
        ablation_heatmap_view["value"],
        errors="raise",
    )

    if bounded_heatmap_metric:
        ablation_heatmap_view["display_value"] = (
            ablation_heatmap_view["display_value"]
            * 100.0
        )

    ablation_matrix = (
        ablation_heatmap_view.pivot(
            index="feature_set",
            columns="model",
            values="display_value",
        )
        .reindex(
            index=feature_order,
            columns=model_order,
        )
    )

    ablation_heatmap_values = (
        ablation_matrix
        .where(
            ablation_matrix.notna(),
            None,
        )
        .values
        .tolist()
    )

    ablation_heatmap_text = []

    for matrix_row in ablation_matrix.itertuples(
        index=False,
        name=None,
    ):
        text_row = []

        for matrix_value in matrix_row:
            if pd.isna(matrix_value):
                text_row.append("")
            elif bounded_heatmap_metric:
                text_row.append(
                    f"{matrix_value:.1f}%"
                )
            else:
                text_row.append(
                    f"{matrix_value:.2f}"
                )

        ablation_heatmap_text.append(text_row)

    available_heatmap_values = (
        ablation_heatmap_view["display_value"]
        .dropna()
        .astype(float)
    )

    heatmap_minimum = float(
        available_heatmap_values.min()
    )

    heatmap_maximum = float(
        available_heatmap_values.max()
    )

    if heatmap_minimum == heatmap_maximum:
        heatmap_minimum = max(
            0.0,
            heatmap_minimum - 0.5,
        )

        heatmap_maximum += 0.5

    lower_is_better = (
        selected_heatmap_metric
        in {
            "MAE",
            "RMSE",
        }
    )

    if lower_is_better:
        ablation_colorscale = [
            [0.0, "#1F8A70"],
            [0.5, "#C9A961"],
            [1.0, "#D65D66"],
        ]

        ablation_direction_note = (
            "Lower scores indicate stronger performance."
        )
    else:
        ablation_colorscale = [
            [0.0, "#D65D66"],
            [0.5, "#C9A961"],
            [1.0, "#1F8A70"],
        ]

        ablation_direction_note = (
            "Higher scores indicate stronger performance."
        )

    selected_heatmap_label = (
        ablation_heatmap_labels[
            selected_heatmap_metric
        ]
    )

    heatmap_suffix = (
        "%"
        if bounded_heatmap_metric
        else ""
    )

    ablation_heatmap_figure = go.Figure(
        data=go.Heatmap(
            z=ablation_heatmap_values,
            x=[
                heatmap_model_labels[model]
                for model in model_order
            ],
            y=[
                feature_labels[feature]
                for feature in feature_order
            ],
            text=ablation_heatmap_text,
            texttemplate="%{text}",
            textfont={
                "size": 12,
                "color": "#F8FAFC",
            },
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Model: %{x}<br>"
                + selected_heatmap_label
                + ": %{z:.2f}"
                + heatmap_suffix
                + "<extra></extra>"
            ),
            colorscale=ablation_colorscale,
            zmin=heatmap_minimum,
            zmax=heatmap_maximum,
            xgap=4,
            ygap=4,
            hoverongaps=False,
            colorbar={
                "title": {
                    "text": (
                        "%"
                        if bounded_heatmap_metric
                        else "Score"
                    ),
                },
                "thickness": 14,
            },
        )
    )

    ablation_heatmap_figure = style_figure(
        ablation_heatmap_figure,
        selected_heatmap_label,
        height=455,
    )

    ablation_heatmap_figure.update_layout(
        xaxis={
            "title": "Model",
            "side": "top",
        },
        yaxis={
            "title": "Feature configuration",
            "autorange": "reversed",
        },
        margin={
            "l": 25,
            "r": 25,
            "t": 105,
            "b": 35,
        },
    )

    st.plotly_chart(
        ablation_heatmap_figure,
        width="stretch",
        config={
            "displaylogo": False,
        },
        key=(
            "feature_ablation_heatmap_"
            + selected_heatmap_metric
        ),
    )

    heatmap_note_col, heatmap_download_col = (
        st.columns(
            [
                0.70,
                0.30,
            ]
        )
    )

    with heatmap_note_col:
        st.info(
            ablation_direction_note
            + " Untested model-feature combinations remain blank."
        )

    with heatmap_download_col:
        st.download_button(
            "Download ablation matrix data",
            data=csv_bytes(
                ablation_heatmap_view[
                    [
                        "task",
                        "feature_set",
                        "model",
                        "metric",
                        "value",
                    ]
                ]
            ),
            file_name=(
                "feature_ablation_matrix_"
                + selected_heatmap_metric
                + ".csv"
            ),
            mime="text/csv",
            key=(
                "download_ablation_matrix_"
                + selected_heatmap_metric
            ),
        )


elif selected_section == "Historical error analysis":
    st.subheader("Historical polling-error analysis")

    st.caption(
        "This section uses development elections only. It examines where "
        "the selected polling-average benchmark succeeded, where it missed, "
        "and whether errors differ across elections and countries."
    )

    error_filter_left, error_filter_right = st.columns(2)

    error_countries = sorted(
        development_party_errors["country"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_error_country = error_filter_left.selectbox(
        "Country",
        ["All"] + error_countries,
        format_func=lambda value: (
            value if value == "All" else value.title()
        ),
        key="historical_error_country",
    )

    error_view = development_party_errors.copy()
    election_error_view = development_election_errors.copy()

    if selected_error_country != "All":
        error_view = error_view.loc[
            error_view["country"] == selected_error_country
        ].copy()

        election_error_view = election_error_view.loc[
            election_error_view["country"]
            == selected_error_country
        ].copy()

    available_error_elections = sorted(
        error_view["election_year"]
        .astype(int)
        .unique()
        .tolist()
    )

    selected_error_election = error_filter_right.selectbox(
        "Election scope",
        ["All"] + available_error_elections,
        format_func=lambda value: (
            "All development elections"
            if value == "All"
            else str(value)
        ),
        key="historical_error_election",
    )

    if selected_error_election != "All":
        error_view = error_view.loc[
            error_view["election_year"].astype(int)
            == selected_error_election
        ].copy()

        election_error_view = election_error_view.loc[
            election_error_view["election_year"].astype(int)
            == selected_error_election
        ].copy()

    if error_view.empty:
        st.warning(
            "No development error records match the selected filters."
        )
    else:
        error_observations = int(len(error_view))

        error_elections = int(
            error_view[
                ["country", "election_year"]
            ].drop_duplicates().shape[0]
        )

        mean_absolute_error = float(
            error_view["baseline_abs_error"].mean()
        )

        mean_signed_error = float(
            error_view["baseline_error"].mean()
        )

        maximum_absolute_error = float(
            error_view["baseline_abs_error"].max()
        )

        e1, e2, e3, e4, e5 = st.columns(5)

        e1.metric(
            "Party observations",
            error_observations,
        )

        e2.metric(
            "Elections",
            error_elections,
        )

        e3.metric(
            "Mean absolute error",
            f"{mean_absolute_error:.2f} pp",
        )

        e4.metric(
            "Mean signed error",
            f"{mean_signed_error:+.2f} pp",
        )

        e5.metric(
            "Largest miss",
            f"{maximum_absolute_error:.2f} pp",
        )

        distribution_left, distribution_right = st.columns(2)

        distribution_data = error_view.copy()

        distribution_data["Country"] = (
            distribution_data["country"].str.title()
        )

        distribution_figure = px.histogram(
            distribution_data,
            x="baseline_error",
            color="Country",
            nbins=24,
            marginal="box",
            hover_data={
                "party": True,
                "election_year": True,
                "baseline_abs_error": ":.2f",
            },
            color_discrete_sequence=[
                "#F2B84B",
                "#4EA1FF",
                "#32C7C9",
                "#A78BFA",
            ],
        )

        distribution_figure.add_vline(
            x=0,
            line_dash="dash",
            line_color="rgba(232, 238, 247, 0.65)",
        )

        distribution_figure.update_layout(
            xaxis_title="Signed polling error (percentage points)",
            yaxis_title="Party observations",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )

        with distribution_left:
            st.plotly_chart(
                style_figure(
                    distribution_figure,
                    "Distribution of historical polling errors",
                    height=450,
                ),
                width="stretch",
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
            )

        scatter_data = error_view.copy()

        scatter_data["Country"] = (
            scatter_data["country"].str.title()
        )

        scatter_data["Election"] = (
            scatter_data["country"].str.title()
            + " "
            + scatter_data["election_year"]
            .astype(int)
            .astype(str)
        )

        scatter_figure = px.scatter(
            scatter_data,
            x="baseline_vote_prediction",
            y="actual_pct",
            color="Country",
            size="baseline_abs_error",
            hover_name="party",
            hover_data={
                "Election": True,
                "baseline_error": ":.2f",
                "baseline_abs_error": ":.2f",
                "baseline_vote_prediction": ":.2f",
                "actual_pct": ":.2f",
            },
            color_discrete_sequence=[
                "#F2B84B",
                "#4EA1FF",
                "#32C7C9",
                "#A78BFA",
            ],
        )

        axis_min = float(
            min(
                scatter_data["baseline_vote_prediction"].min(),
                scatter_data["actual_pct"].min(),
            )
        )

        axis_max = float(
            max(
                scatter_data["baseline_vote_prediction"].max(),
                scatter_data["actual_pct"].max(),
            )
        )

        axis_padding = max(
            (axis_max - axis_min) * 0.06,
            0.5,
        )

        axis_min -= axis_padding
        axis_max += axis_padding

        scatter_figure.add_shape(
            type="line",
            x0=axis_min,
            y0=axis_min,
            x1=axis_max,
            y1=axis_max,
            line={
                "dash": "dash",
                "color": "rgba(232, 238, 247, 0.55)",
            },
        )

        scatter_figure.update_layout(
            xaxis_title="Final polling average (%)",
            yaxis_title="Actual result (%)",
            xaxis_range=[axis_min, axis_max],
            yaxis_range=[axis_min, axis_max],
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )

        with distribution_right:
            st.plotly_chart(
                style_figure(
                    scatter_figure,
                    "Polling average versus actual result",
                    height=450,
                ),
                width="stretch",
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
            )

        st.markdown("### Election-level error and winner outcome")

        election_chart_data = election_error_view.copy()

        election_chart_data["Election"] = (
            election_chart_data["country"].str.title()
            + " "
            + election_chart_data["election_year"]
            .astype(int)
            .astype(str)
        )

        election_chart_data["Winner result"] = (
            election_chart_data["winner_correct"]
            .astype(int)
            .map(
                {
                    1: "Correct",
                    0: "Miss",
                }
            )
        )

        election_chart_data = election_chart_data.sort_values(
            [
                "country",
                "election_year",
            ]
        )

        election_figure = px.bar(
            election_chart_data,
            x="Election",
            y="election_baseline_mae",
            color="Winner result",
            text_auto=".2f",
            hover_data={
                "actual_winner": True,
                "polling_winner": True,
                "actual_margin": ":.2f",
                "polling_margin": ":.2f",
                "election_ridge_mae": ":.2f",
            },
            color_discrete_map={
                "Correct": "#32C7C9",
                "Miss": "#F26B6B",
            },
        )

        election_figure.update_layout(
            xaxis_title="",
            yaxis_title="Election mean absolute error (pp)",
            xaxis_tickangle=-35,
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )

        st.plotly_chart(
            style_figure(
                election_figure,
                "Development election error profile",
                height=500,
            ),
            width="stretch",
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

        table_left, table_right = st.columns(2)

        with table_left:
            st.markdown("### Largest polling misses")

            largest_error_rows = (
                error_view
                .nlargest(
                    15,
                    "baseline_abs_error",
                )
                .copy()
            )

            largest_error_rows["country"] = (
                largest_error_rows["country"].str.title()
            )

            largest_error_rows = largest_error_rows[
                [
                    "country",
                    "election_year",
                    "party",
                    "actual_pct",
                    "baseline_vote_prediction",
                    "baseline_error",
                    "baseline_abs_error",
                ]
            ].rename(
                columns={
                    "country": "Country",
                    "election_year": "Election",
                    "party": "Party",
                    "actual_pct": "Actual result",
                    "baseline_vote_prediction": "Polling average",
                    "baseline_error": "Signed error",
                    "baseline_abs_error": "Absolute error",
                }
            )

            st.dataframe(
                largest_error_rows,
                width="stretch",
                hide_index=True,
                height=455,
                column_config={
                    "Actual result": st.column_config.NumberColumn(
                        format="%.2f%%",
                    ),
                    "Polling average": st.column_config.NumberColumn(
                        format="%.2f%%",
                    ),
                    "Signed error": st.column_config.NumberColumn(
                        format="%+.2f pp",
                    ),
                    "Absolute error": st.column_config.NumberColumn(
                        format="%.2f pp",
                    ),
                },
            )

        with table_right:
            st.markdown("### Election summary")

            election_summary = election_chart_data[
                [
                    "country",
                    "election_year",
                    "actual_winner",
                    "polling_winner",
                    "Winner result",
                    "election_baseline_mae",
                    "election_ridge_mae",
                ]
            ].copy()

            election_summary["country"] = (
                election_summary["country"].str.title()
            )

            election_summary = election_summary.rename(
                columns={
                    "country": "Country",
                    "election_year": "Election",
                    "actual_winner": "Actual winner",
                    "polling_winner": "Polling winner",
                    "election_baseline_mae": "Polling-average MAE",
                    "election_ridge_mae": "Ridge MAE",
                }
            )

            st.dataframe(
                election_summary,
                width="stretch",
                hide_index=True,
                height=455,
                column_config={
                    "Polling-average MAE": st.column_config.NumberColumn(
                        format="%.2f pp",
                    ),
                    "Ridge MAE": st.column_config.NumberColumn(
                        format="%.2f pp",
                    ),
                },
            )

        st.download_button(
            "Download filtered development errors",
            data=csv_bytes(error_view),
            file_name="development_polling_errors_filtered.csv",
            mime="text/csv",
        )



    # DYNAMIC TRAJECTORY AND ERROR EXPLORER V3
    st.markdown("### Interactive polling trajectory explorer")

    st.caption(
        "Explore individual poll observations, rolling polling "
        "averages and modelled election results through time. "
        "This is a historical explorer and does not retrain or "
        "modify the frozen evaluation."
    )

    trajectory_country_options = sorted(
        polling_trajectory[
            "country_label"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    trajectory_filter_1, trajectory_filter_2 = (
        st.columns(2)
    )

    selected_trajectory_country = (
        trajectory_filter_1.selectbox(
            "Trajectory country",
            trajectory_country_options,
            key="trajectory_country",
        )
    )

    country_trajectory = polling_trajectory.loc[
        polling_trajectory["country_label"]
        == selected_trajectory_country
    ].copy()

    trajectory_year_options = sorted(
        country_trajectory["election_year"]
        .astype(int)
        .unique()
        .tolist(),
        reverse=True,
    )

    selected_trajectory_year = (
        trajectory_filter_2.selectbox(
            "Trajectory election",
            trajectory_year_options,
            format_func=lambda value: str(value),
            key="trajectory_election_year",
        )
    )

    trajectory_election = (
        country_trajectory.loc[
            country_trajectory[
                "election_year"
            ].astype(int)
            == selected_trajectory_year
        ]
        .copy()
    )

    trajectory_election["poll_date"] = (
        pd.to_datetime(
            trajectory_election["poll_date"],
            errors="raise",
        )
    )

    trajectory_election[
        "model_included_boolean"
    ] = (
        trajectory_election["model_included"]
        .astype(str)
        .str.lower()
        .eq("true")
    )

    trajectory_party_options = sorted(
        trajectory_election["party"]
        .dropna()
        .unique()
        .tolist()
    )

    default_trajectory_parties = sorted(
        trajectory_election.loc[
            trajectory_election[
                "model_included_boolean"
            ],
            "party",
        ]
        .dropna()
        .unique()
        .tolist()
    )

    if not default_trajectory_parties:
        default_trajectory_parties = (
            trajectory_party_options[:4]
        )

    selected_trajectory_parties = st.multiselect(
        "Parties",
        options=trajectory_party_options,
        default=default_trajectory_parties,
        key="trajectory_parties",
    )

    trajectory_control_1, trajectory_control_2 = (
        st.columns(2)
    )

    show_raw_poll_observations = (
        trajectory_control_1.checkbox(
            "Show raw poll observations",
            value=True,
            key="trajectory_show_raw",
        )
    )

    show_actual_result_markers = (
        trajectory_control_2.checkbox(
            "Show election-result markers",
            value=True,
            key="trajectory_show_actual",
        )
    )

    if not selected_trajectory_parties:
        st.warning(
            "Select at least one party to render the "
            "polling trajectory."
        )
    else:
        trajectory_plot = trajectory_election.loc[
            trajectory_election["party"].isin(
                selected_trajectory_parties
            )
        ].copy()

        trajectory_plot = trajectory_plot.sort_values(
            [
                "party",
                "poll_date",
            ]
        )

        trajectory_observations = int(
            len(trajectory_plot)
        )

        trajectory_date_min = (
            trajectory_plot["poll_date"].min()
        )

        trajectory_date_max = (
            trajectory_plot["poll_date"].max()
        )

        trajectory_span_days = int(
            (
                trajectory_date_max
                - trajectory_date_min
            ).days
        )

        trajectory_split = str(
            trajectory_plot[
                "dataset_split"
            ].iloc[0]
        ).title()

        t1, t2, t3, t4 = st.columns(4)

        t1.metric(
            "Poll-party observations",
            f"{trajectory_observations:,}",
        )

        t2.metric(
            "Selected parties",
            len(selected_trajectory_parties),
        )

        t3.metric(
            "Campaign span",
            f"{trajectory_span_days:,} days",
        )

        t4.metric(
            "Evaluation split",
            trajectory_split,
        )

        trajectory_figure = px.line(
            trajectory_plot,
            x="poll_date",
            y="rolling_avg",
            color="party",
            line_group="party",
            custom_data=[
                "country_label",
                "election_year",
                "party",
                "pct",
                "rolling_avg",
                "dataset_split",
                "actual_pct",
                "model_included_boolean",
            ],
            labels={
                "poll_date": "Poll date",
                "rolling_avg": (
                    "Rolling polling average (%)"
                ),
                "party": "Party",
            },
            color_discrete_sequence=[
                "#F2B84B",
                "#4EA1FF",
                "#32C7C9",
                "#A78BFA",
                "#F26B6B",
                "#7ED957",
                "#F59EBC",
                "#94A3B8",
            ],
        )

        trajectory_figure.update_traces(
            line={
                "width": 3.0,
            },
            hovertemplate=(
                "<b>%{customdata[2]}</b><br>"
                "Date: %{x|%d %b %Y}<br>"
                "Rolling average: %{y:.2f}%<br>"
                "Raw observation: "
                "%{customdata[3]:.2f}%<br>"
                "Evaluation split: "
                "%{customdata[5]}<br>"
                "Actual result: "
                "%{customdata[6]:.2f}%"
                "<extra></extra>"
            ),
        )

        trajectory_party_colours = {
            trace.name: trace.line.color
            for trace in trajectory_figure.data
        }

        if show_raw_poll_observations:
            for party_name in (
                selected_trajectory_parties
            ):
                raw_party_rows = (
                    trajectory_plot.loc[
                        trajectory_plot["party"]
                        == party_name
                    ]
                )

                trajectory_figure.add_trace(
                    go.Scatter(
                        x=raw_party_rows[
                            "poll_date"
                        ],
                        y=raw_party_rows["pct"],
                        mode="markers",
                        name=(
                            f"{party_name} raw polls"
                        ),
                        legendgroup=party_name,
                        showlegend=False,
                        marker={
                            "size": 5,
                            "opacity": 0.22,
                            "color": (
                                trajectory_party_colours
                                .get(
                                    party_name,
                                    "#94A3B8",
                                )
                            ),
                        },
                        customdata=(
                            raw_party_rows[
                                [
                                    "party",
                                    "rolling_avg",
                                ]
                            ].to_numpy()
                        ),
                        hovertemplate=(
                            "<b>%{customdata[0]}"
                            "</b><br>"
                            "Date: %{x|%d %b %Y}"
                            "<br>"
                            "Poll observation: "
                            "%{y:.2f}%<br>"
                            "Rolling average: "
                            "%{customdata[1]:.2f}%"
                            "<extra></extra>"
                        ),
                    )
                )

        if show_actual_result_markers:
            for party_name in (
                selected_trajectory_parties
            ):
                party_rows = (
                    trajectory_plot.loc[
                        trajectory_plot["party"]
                        == party_name
                    ]
                )

                actual_results = (
                    party_rows["actual_pct"]
                    .dropna()
                    .unique()
                    .tolist()
                )

                if not actual_results:
                    continue

                actual_result = float(
                    actual_results[0]
                )

                trajectory_figure.add_trace(
                    go.Scatter(
                        x=[
                            trajectory_date_max
                        ],
                        y=[
                            actual_result
                        ],
                        mode="markers",
                        name=(
                            f"{party_name} actual"
                        ),
                        legendgroup=party_name,
                        showlegend=False,
                        marker={
                            "size": 13,
                            "symbol": "diamond",
                            "color": (
                                trajectory_party_colours
                                .get(
                                    party_name,
                                    "#F8FAFC",
                                )
                            ),
                            "line": {
                                "color": "#F8FAFC",
                                "width": 1.5,
                            },
                        },
                        hovertemplate=(
                            f"<b>{party_name}</b>"
                            "<br>"
                            "Election result: "
                            f"{actual_result:.2f}%"
                            "<extra></extra>"
                        ),
                    )
                )

        trajectory_title = (
            f"{selected_trajectory_country} "
            f"{selected_trajectory_year}: "
            "polling observations and rolling averages"
        )

        trajectory_figure = style_figure(
            trajectory_figure,
            trajectory_title,
            height=620,
        )

        trajectory_figure.update_layout(
            hovermode="x unified",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
            margin={
                "l": 25,
                "r": 25,
                "t": 105,
                "b": 75,
            },
            xaxis_rangeslider={
                "visible": True,
                "thickness": 0.08,
                "bgcolor": (
                    "rgba(12, 30, 52, 0.72)"
                ),
            },
        )

        trajectory_figure.update_xaxes(
            title="Poll date",
            rangeselector={
                "buttons": [
                    {
                        "count": 3,
                        "label": "3m",
                        "step": "month",
                        "stepmode": "backward",
                    },
                    {
                        "count": 6,
                        "label": "6m",
                        "step": "month",
                        "stepmode": "backward",
                    },
                    {
                        "count": 1,
                        "label": "1y",
                        "step": "year",
                        "stepmode": "backward",
                    },
                    {
                        "step": "all",
                        "label": "All",
                    },
                ],
                "bgcolor": (
                    "rgba(17, 41, 70, 0.86)"
                ),
                "activecolor": (
                    "rgba(78, 161, 255, 0.45)"
                ),
                "font": {
                    "color": "#E8EEF7",
                },
            },
        )

        trajectory_figure.update_yaxes(
            title="Polling support (%)",
        )

        st.plotly_chart(
            trajectory_figure,
            width="stretch",
            config={
                "displaylogo": False,
                "scrollZoom": True,
            },
            key=(
                "polling_trajectory_"
                + selected_trajectory_country
                .lower()
                .replace(" ", "_")
                + "_"
                + str(
                    selected_trajectory_year
                )
            ),
        )

        trajectory_note_col, trajectory_download_col = (
            st.columns(
                [
                    0.70,
                    0.30,
                ]
            )
        )

        with trajectory_note_col:
            st.info(
                "Solid lines are rolling averages and faint "
                "points are individual poll-party observations. "
                "Terminal diamonds show available election "
                "results at the last observed poll date for visual "
                "comparison; they do not represent an exact "
                "election-day timestamp. Parties not included in "
                "the final model may still appear as historical "
                "polling evidence."
            )

        with trajectory_download_col:
            st.download_button(
                "Download selected trajectory",
                data=csv_bytes(
                    trajectory_plot.drop(
                        columns=[
                            "model_included_boolean",
                        ],
                        errors="ignore",
                    )
                ),
                file_name=(
                    selected_trajectory_country
                    .lower()
                    .replace(" ", "_")
                    + "_"
                    + str(
                        selected_trajectory_year
                    )
                    + "_polling_trajectory.csv"
                ),
                mime="text/csv",
                key="download_selected_trajectory",
            )

    st.markdown(
        "### Error distribution and evidence density"
    )

    st.caption(
        "The violin plot shows the complete party-level error "
        "distribution. The bubble chart compares polling volume "
        "with absolute error; bubble area represents polling "
        "variability. These are descriptive relationships and "
        "must not be interpreted as causal effects."
    )

    error_filter_1, error_filter_2, error_filter_3 = (
        st.columns(3)
    )

    selected_distribution_split = (
        error_filter_1.selectbox(
            "Evaluation split",
            [
                "All",
                "Development",
                "Holdout",
            ],
            key="distribution_split",
        )
    )

    distribution_country_options = sorted(
        party_error_distribution[
            "country_label"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    selected_distribution_country = (
        error_filter_2.selectbox(
            "Distribution country",
            [
                "All",
                *distribution_country_options,
            ],
            key="distribution_country",
        )
    )

    distribution_role_options = sorted(
        party_error_distribution[
            "party_role"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    selected_distribution_role = (
        error_filter_3.selectbox(
            "Party role",
            [
                "All",
                *distribution_role_options,
            ],
            key="distribution_party_role",
        )
    )

    distribution_view = (
        party_error_distribution.copy()
    )

    if selected_distribution_split != "All":
        distribution_view = (
            distribution_view.loc[
                distribution_view[
                    "evaluation_split"
                ]
                == selected_distribution_split
            ].copy()
        )

    if selected_distribution_country != "All":
        distribution_view = (
            distribution_view.loc[
                distribution_view[
                    "country_label"
                ]
                == selected_distribution_country
            ].copy()
        )

    if selected_distribution_role != "All":
        distribution_view = (
            distribution_view.loc[
                distribution_view[
                    "party_role"
                ]
                == selected_distribution_role
            ].copy()
        )

    if distribution_view.empty:
        st.warning(
            "No party-error records match the current "
            "distribution filters."
        )
    else:
        distribution_view[
            "absolute_error"
        ] = pd.to_numeric(
            distribution_view[
                "absolute_error"
            ],
            errors="raise",
        )

        distribution_view[
            "n_poll_observations"
        ] = pd.to_numeric(
            distribution_view[
                "n_poll_observations"
            ],
            errors="raise",
        )

        distribution_view[
            "bubble_size"
        ] = pd.to_numeric(
            distribution_view[
                "bubble_size"
            ],
            errors="raise",
        )

        distribution_view[
            "poll_std"
        ] = pd.to_numeric(
            distribution_view[
                "poll_std"
            ],
            errors="coerce",
        )

        distribution_median = float(
            distribution_view[
                "absolute_error"
            ].median()
        )

        distribution_left, distribution_right = (
            st.columns(2)
        )

        error_violin_figure = px.violin(
            distribution_view,
            x="country_label",
            y="absolute_error",
            color="evaluation_split",
            box=True,
            points="all",
            hover_name="party",
            hover_data={
                "election_label": True,
                "party_role": True,
                "actual_pct": ":.2f",
                "predicted_pct": ":.2f",
                "signed_error": ":+.2f",
                "absolute_error": ":.2f",
                "n_poll_observations": ":,",
                "poll_std": ":.2f",
            },
            labels={
                "country_label": "Country",
                "absolute_error": (
                    "Absolute polling error (pp)"
                ),
                "evaluation_split": (
                    "Evaluation split"
                ),
                "election_label": "Election",
                "party_role": "Party role",
                "actual_pct": "Actual result (%)",
                "predicted_pct": (
                    "Polling prediction (%)"
                ),
                "signed_error": (
                    "Signed error (pp)"
                ),
                "n_poll_observations": (
                    "Poll observations"
                ),
                "poll_std": (
                    "Polling standard deviation"
                ),
            },
            color_discrete_map={
                "Development": "#4EA1FF",
                "Holdout": "#F2B84B",
            },
            category_orders={
                "country_label": [
                    "Australia",
                    "Canada",
                    "United Kingdom",
                    "United States",
                ],
                "evaluation_split": [
                    "Development",
                    "Holdout",
                ],
            },
        )

        # DYNAMIC VISUAL QA V4
        error_violin_figure.update_traces(
            meanline_visible=True,
            spanmode="hard",
            scalemode="width",
            opacity=0.78,
            jitter=0.12,
            marker={
                "size": 6,
                "opacity": 0.68,
            },
        )

        error_violin_figure.add_hline(
            y=distribution_median,
            line_dash="dash",
            line_color=(
                "rgba(232, 238, 247, 0.60)"
            ),
            annotation_text=(
                "Filtered median "
                f"{distribution_median:.2f} pp"
            ),
            annotation_position="top right",
        )

        error_violin_figure = style_figure(
            error_violin_figure,
            "Party-level absolute-error distribution",
            height=520,
        )

        error_violin_figure.update_layout(
            xaxis_title="",
            yaxis_title=(
                "Absolute polling error "
                "(percentage points)"
            ),
            legend={
                "orientation": "h",
                "yanchor": "top",
                "y": -0.18,
                "xanchor": "center",
                "x": 0.5,
                "font": {
                    "size": 10,
                },
            },
            margin={
                "l": 25,
                "r": 25,
                "t": 82,
                "b": 112,
            },
        )

        error_violin_figure.update_yaxes(
            rangemode="tozero",
        )

        with distribution_left:
            st.plotly_chart(
                error_violin_figure,
                width="stretch",
                config={
                    "displaylogo": False,
                },
                key="party_error_violin",
            )

        volume_error_figure = px.scatter(
            distribution_view,
            x="n_poll_observations",
            y="absolute_error",
            size="bubble_size",
            color="country_label",
            symbol="evaluation_split",
            hover_name="party",
            hover_data={
                "election_label": True,
                "party_role": True,
                "actual_pct": ":.2f",
                "predicted_pct": ":.2f",
                "signed_error": ":+.2f",
                "absolute_error": ":.2f",
                "n_poll_observations": ":,",
                "poll_std": ":.2f",
                "campaign_span_days": ":,",
                "recent_30d_observations": ":,",
                "bubble_size": False,
            },
            labels={
                "n_poll_observations": (
                    "Poll observations"
                ),
                "absolute_error": (
                    "Absolute polling error (pp)"
                ),
                "country_label": "Country",
                "evaluation_split": (
                    "Evaluation split"
                ),
                "election_label": "Election",
                "party_role": "Party role",
                "actual_pct": "Actual result (%)",
                "predicted_pct": (
                    "Polling prediction (%)"
                ),
                "signed_error": (
                    "Signed error (pp)"
                ),
                "poll_std": (
                    "Polling standard deviation"
                ),
                "campaign_span_days": (
                    "Campaign span (days)"
                ),
                "recent_30d_observations": (
                    "Recent 30-day observations"
                ),
            },
            size_max=38,
            color_discrete_sequence=[
                "#F2B84B",
                "#4EA1FF",
                "#32C7C9",
                "#A78BFA",
            ],
            category_orders={
                "country_label": [
                    "Australia",
                    "Canada",
                    "United Kingdom",
                    "United States",
                ],
                "evaluation_split": [
                    "Development",
                    "Holdout",
                ],
            },
        )

        volume_error_figure.update_traces(
            marker={
                "opacity": 0.78,
                "line": {
                    "color": (
                        "rgba(235, 241, 250, 0.70)"
                    ),
                    "width": 0.9,
                },
            },
        )

        volume_error_figure.add_hline(
            y=distribution_median,
            line_dash="dash",
            line_color=(
                "rgba(232, 238, 247, 0.48)"
            ),
        )

        volume_error_figure = style_figure(
            volume_error_figure,
            "Polling volume versus absolute error",
            height=520,
        )

        volume_error_figure.update_layout(
            xaxis_title=(
                "Number of poll observations"
            ),
            yaxis_title=(
                "Absolute polling error "
                "(percentage points)"
            ),
            legend={
                "orientation": "h",
                "yanchor": "top",
                "y": -0.18,
                "xanchor": "center",
                "x": 0.5,
                "font": {
                    "size": 9,
                },
            },
            margin={
                "l": 25,
                "r": 25,
                "t": 82,
                "b": 135,
            },
        )

        volume_error_figure.update_yaxes(
            rangemode="tozero",
        )

        with distribution_right:
            st.plotly_chart(
                volume_error_figure,
                width="stretch",
                config={
                    "displaylogo": False,
                    "scrollZoom": True,
                },
                key="polling_volume_error_bubbles",
            )

        distribution_note_col, distribution_download_col = (
            st.columns(
                [
                    0.70,
                    0.30,
                ]
            )
        )

        with distribution_note_col:
            st.info(
                "A larger bubble means greater within-campaign "
                "polling variability, not greater electoral "
                "importance. The chart is an exploratory "
                "diagnostic and does not establish that polling "
                "volume or volatility causes forecast error."
            )

        with distribution_download_col:
            st.download_button(
                "Download filtered error evidence",
                data=csv_bytes(
                    distribution_view
                ),
                file_name=(
                    "party_error_distribution_filtered.csv"
                ),
                mime="text/csv",
                key=(
                    "download_filtered_error_distribution"
                ),
            )


elif selected_section == "Polling-scope audit":
    st.subheader("National polling-scope audit")

    st.caption(
        "This audit records the source-table review completed before "
        "feature engineering. Uncertain or out-of-scope tables remain "
        "excluded unless explicitly approved through the documented process."
    )

    scope_view = scope_audit.copy()

    scope_view["scope_status"] = (
        scope_view["scope_status"]
        .fillna("unclassified")
        .astype(str)
    )

    scope_view["scope_reason"] = (
        scope_view["scope_reason"]
        .fillna("")
        .astype(str)
    )

    scope_view["country"] = (
        scope_view["country"]
        .fillna("unknown")
        .astype(str)
    )

    scope_filter_1, scope_filter_2, scope_filter_3 = st.columns(3)

    available_scope_countries = sorted(
        scope_view["country"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_scope_country = scope_filter_1.selectbox(
        "Country",
        ["All"] + available_scope_countries,
        format_func=lambda value: (
            value if value == "All" else value.title()
        ),
        key="scope_audit_country",
    )

    available_scope_statuses = sorted(
        scope_view["scope_status"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_scope_status = scope_filter_2.selectbox(
        "Scope status",
        ["All"] + available_scope_statuses,
        format_func=lambda value: (
            value
            if value == "All"
            else value.replace("_", " ").title()
        ),
        key="scope_audit_status",
    )

    available_scope_years = sorted(
        scope_view["election_year"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    selected_scope_year = scope_filter_3.selectbox(
        "Election year",
        ["All"] + available_scope_years,
        format_func=lambda value: (
            "All election years"
            if value == "All"
            else str(value)
        ),
        key="scope_audit_year",
    )

    if selected_scope_country != "All":
        scope_view = scope_view.loc[
            scope_view["country"] == selected_scope_country
        ].copy()

    if selected_scope_status != "All":
        scope_view = scope_view.loc[
            scope_view["scope_status"] == selected_scope_status
        ].copy()

    if selected_scope_year != "All":
        scope_view = scope_view.loc[
            scope_view["election_year"].astype(int)
            == selected_scope_year
        ].copy()

    if scope_view.empty:
        st.warning(
            "No polling-scope audit records match the selected filters."
        )
    else:
        audited_tables = int(len(scope_view))

        audited_countries = int(
            scope_view["country"].nunique()
        )

        audited_elections = int(
            scope_view[
                ["country", "election_year"]
            ].drop_duplicates().shape[0]
        )

        audited_rows = int(
            scope_view["poll_party_rows"]
            .fillna(0)
            .sum()
        )

        status_categories = int(
            scope_view["scope_status"].nunique()
        )

        s1, s2, s3, s4, s5 = st.columns(5)

        s1.metric(
            "Source tables",
            audited_tables,
        )

        s2.metric(
            "Countries",
            audited_countries,
        )

        s3.metric(
            "Elections",
            audited_elections,
        )

        s4.metric(
            "Poll-party rows",
            f"{audited_rows:,}",
        )

        s5.metric(
            "Status categories",
            status_categories,
        )

        status_summary = (
            scope_view.groupby(
                "scope_status",
                as_index=False,
            )
            .agg(
                source_tables=("source_table", "count"),
                poll_party_rows=("poll_party_rows", "sum"),
                countries=("country", "nunique"),
            )
            .sort_values(
                "poll_party_rows",
                ascending=False,
            )
        )

        status_summary["Scope status"] = (
            status_summary["scope_status"]
            .str.replace("_", " ", regex=False)
            .str.title()
        )

        status_figure = px.bar(
            status_summary,
            x="Scope status",
            y="poll_party_rows",
            color="Scope status",
            text_auto=".0f",
            hover_data={
                "source_tables": True,
                "countries": True,
                "scope_status": False,
            },
            color_discrete_sequence=[
                "#32C7C9",
                "#F2B84B",
                "#4EA1FF",
                "#A78BFA",
                "#F26B6B",
                "#7ED957",
            ],
        )

        status_figure.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Poll-party rows reviewed",
            xaxis_tickangle=-20,
        )

        country_status = (
            scope_view.groupby(
                [
                    "country",
                    "scope_status",
                ],
                as_index=False,
            )
            .agg(
                source_tables=("source_table", "count"),
                poll_party_rows=("poll_party_rows", "sum"),
            )
        )

        country_status["Country"] = (
            country_status["country"].str.title()
        )

        country_status["Scope status"] = (
            country_status["scope_status"]
            .str.replace("_", " ", regex=False)
            .str.title()
        )

        country_figure = px.bar(
            country_status,
            x="Country",
            y="source_tables",
            color="Scope status",
            barmode="stack",
            text_auto=".0f",
            hover_data={
                "poll_party_rows": True,
                "country": False,
                "scope_status": False,
            },
            color_discrete_sequence=[
                "#32C7C9",
                "#F2B84B",
                "#4EA1FF",
                "#A78BFA",
                "#F26B6B",
                "#7ED957",
            ],
        )

        country_figure.update_layout(
            xaxis_title="",
            yaxis_title="Source tables reviewed",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )

        chart_left, chart_right = st.columns(2)

        with chart_left:
            st.plotly_chart(
                style_figure(
                    status_figure,
                    "Rows reviewed by scope decision",
                    height=450,
                ),
                width="stretch",
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
            )

        with chart_right:
            st.plotly_chart(
                style_figure(
                    country_figure,
                    "Source-table decisions by country",
                    height=450,
                ),
                width="stretch",
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
            )

        st.markdown("### Filtered source-table decisions")

        audit_display = scope_view.copy()

        audit_display["country"] = (
            audit_display["country"].str.title()
        )

        audit_display["scope_status"] = (
            audit_display["scope_status"]
            .str.replace("_", " ", regex=False)
            .str.title()
        )

        audit_display = audit_display[
            [
                "country",
                "election_year",
                "source_table",
                "poll_party_rows",
                "party_count",
                "scope_status",
                "scope_reason",
                "marker_candidate_count",
                "best_marker_date_raw",
                "best_marker_relevance",
                "national_overlap_parties",
                "marker_mae",
                "marker_max_abs_error",
            ]
        ].rename(
            columns={
                "country": "Country",
                "election_year": "Election",
                "source_table": "Source table",
                "poll_party_rows": "Poll-party rows",
                "party_count": "Party count",
                "scope_status": "Scope status",
                "scope_reason": "Scope reason",
                "marker_candidate_count": "Marker candidates",
                "best_marker_date_raw": "Best marker",
                "best_marker_relevance": "Marker relevance",
                "national_overlap_parties": "National overlap",
                "marker_mae": "Marker MAE",
                "marker_max_abs_error": "Marker maximum error",
            }
        ).sort_values(
            [
                "Country",
                "Election",
                "Source table",
            ]
        )

        st.dataframe(
            audit_display,
            width="stretch",
            hide_index=True,
            height=520,
            column_config={
                "Poll-party rows": st.column_config.NumberColumn(
                    format="%d",
                ),
                "Party count": st.column_config.NumberColumn(
                    format="%d",
                ),
                "Marker candidates": st.column_config.NumberColumn(
                    format="%d",
                ),
                "National overlap": st.column_config.NumberColumn(
                    format="%d",
                ),
                "Marker MAE": st.column_config.NumberColumn(
                    format="%.3f",
                ),
                "Marker maximum error": st.column_config.NumberColumn(
                    format="%.3f",
                ),
            },
        )

        st.download_button(
            "Download filtered scope audit",
            data=csv_bytes(scope_view),
            file_name="polling_table_scope_audit_filtered.csv",
            mime="text/csv",
        )

        st.info(
            "The scope audit is governance evidence. Changing a filter "
            "only changes the displayed records; it does not alter the "
            "frozen datasets, selected method, or holdout evaluation."
        )



    # SCOPE DONUT AND TREEMAP V2
    st.markdown(
        "### Polling-scope composition"
    )

    st.caption(
        "The donut shows the part-to-whole distribution of "
        "poll-party rows. The interactive treemap exposes the "
        "country, scope-decision and source-table hierarchy."
    )

    if scope_view.empty:
        st.warning(
            "No scope records match the current filters."
        )
    else:
        scope_visual = scope_view.copy()

        scope_visual["poll_party_rows"] = pd.to_numeric(
            scope_visual["poll_party_rows"],
            errors="coerce",
        ).fillna(0)

        scope_status_labels = {
            "review": "Review",
            "approved_marker_match": (
                "Approved marker match"
            ),
            "rejected_marker_mismatch": (
                "Rejected marker mismatch"
            ),
        }

        scope_country_labels = {
            "australia": "Australia",
            "canada": "Canada",
            "uk": "United Kingdom",
            "us": "United States",
        }

        scope_visual["status_label"] = (
            scope_visual["scope_status"]
            .map(scope_status_labels)
            .fillna(
                scope_visual["scope_status"]
            )
        )

        scope_visual["country_label"] = (
            scope_visual["country"]
            .map(scope_country_labels)
            .fillna(
                scope_visual["country"]
            )
        )

        scope_composition = (
            scope_visual.groupby(
                [
                    "scope_status",
                    "status_label",
                ],
                as_index=False,
            )
            .agg(
                source_tables=(
                    "source_table",
                    "count",
                ),
                poll_party_rows=(
                    "poll_party_rows",
                    "sum",
                ),
            )
            .sort_values(
                "poll_party_rows",
                ascending=False,
            )
        )

        scope_donut_col, scope_treemap_col = (
            st.columns(
                [
                    0.38,
                    0.62,
                ]
            )
        )

        with scope_donut_col:
            scope_donut_figure = px.pie(
                scope_composition,
                names="status_label",
                values="poll_party_rows",
                hole=0.60,
                custom_data=[
                    "source_tables",
                ],
                labels={
                    "status_label": "Scope decision",
                    "poll_party_rows": (
                        "Poll-party rows"
                    ),
                    "source_tables": "Source tables",
                },
                color_discrete_sequence=[
                    "#32C7C9",
                    "#F2B84B",
                    "#4EA1FF",
                ],
            )

            scope_donut_figure.update_traces(
                textposition="inside",
                textinfo="percent",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Poll-party rows: %{value:,}<br>"
                    "Share: %{percent}<br>"
                    "Source tables: "
                    "%{customdata[0]:,}"
                    "<extra></extra>"
                ),
                marker={
                    "line": {
                        "color": (
                            "rgba(235, 241, 250, 0.70)"
                        ),
                        "width": 1,
                    },
                },
            )

            scope_donut_figure = style_figure(
                scope_donut_figure,
                "Rows by scope decision",
                height=500,
            )

            scope_donut_figure.update_layout(
                legend={
                    "orientation": "h",
                    "yanchor": "top",
                    "y": -0.04,
                    "xanchor": "center",
                    "x": 0.5,
                },
                margin={
                    "l": 10,
                    "r": 10,
                    "t": 80,
                    "b": 80,
                },
                annotations=[
                    {
                        "text": (
                            f"{int(scope_visual['poll_party_rows'].sum()):,}"
                            "<br><span style='font-size:11px'>"
                            "poll-party rows</span>"
                        ),
                        "x": 0.5,
                        "y": 0.5,
                        "showarrow": False,
                        "font": {
                            "size": 17,
                            "color": "#F8FAFC",
                        },
                    }
                ],
            )

            st.plotly_chart(
                scope_donut_figure,
                width="stretch",
                config={
                    "displaylogo": False,
                },
                key="scope_status_donut",
            )

        with scope_treemap_col:
            scope_treemap_figure = px.treemap(
                scope_visual,
                path=[
                    "country_label",
                    "status_label",
                    "source_table",
                ],
                values="poll_party_rows",
                color="status_label",
                hover_data={
                    "country_label": False,
                    "status_label": False,
                    "source_table": True,
                    "poll_party_rows": ":,",
                    "election_year": True,
                    "party_count": ":,",
                    "marker_candidate_count": ":,",
                    "national_overlap_parties": ":,",
                },
                labels={
                    "country_label": "Country",
                    "status_label": "Scope decision",
                    "source_table": "Source table",
                    "poll_party_rows": (
                        "Poll-party rows"
                    ),
                    "election_year": "Election year",
                    "party_count": "Party count",
                    "marker_candidate_count": (
                        "Marker candidates"
                    ),
                    "national_overlap_parties": (
                        "National overlap"
                    ),
                },
                color_discrete_sequence=[
                    "#32C7C9",
                    "#F2B84B",
                    "#4EA1FF",
                ],
            )

            scope_treemap_figure.update_traces(
                root_color="rgba(10, 25, 47, 0.65)",
                maxdepth=3,
                marker={
                    "line": {
                        "color": (
                            "rgba(235, 241, 250, 0.24)"
                        ),
                        "width": 1,
                    },
                },
                textfont={
                    "color": "#F8FAFC",
                },
            )

            scope_treemap_figure = style_figure(
                scope_treemap_figure,
                "Scope hierarchy by country and source table",
                height=500,
            )

            scope_treemap_figure.update_layout(
                margin={
                    "l": 8,
                    "r": 8,
                    "t": 80,
                    "b": 8,
                },
            )

            st.plotly_chart(
                scope_treemap_figure,
                width="stretch",
                config={
                    "displaylogo": False,
                },
                key="scope_country_status_treemap",
            )

        scope_note_col, scope_download_col = (
            st.columns(
                [
                    0.70,
                    0.30,
                ]
            )
        )

        with scope_note_col:
            st.info(
                "Click a treemap branch to drill into a country, "
                "scope decision or individual source table."
            )

        with scope_download_col:
            st.download_button(
                "Download scope composition",
                data=csv_bytes(
                    scope_composition
                ),
                file_name=(
                    "polling_scope_composition.csv"
                ),
                mime="text/csv",
                key="download_scope_composition",
            )


elif selected_section == "Chronological holdout":
    st.subheader("Interactive chronological holdout explorer")

    filter_left, filter_right = st.columns(2)

    available_countries = sorted(
        holdout_elections["country"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_country = filter_left.selectbox(
        "Country",
        available_countries,
        format_func=str.title,
        key="holdout_country",
    )

    country_elections = holdout_elections.loc[
        holdout_elections["country"] == selected_country
    ].copy()

    available_years = sorted(
        country_elections["election_year"]
        .astype(int)
        .unique()
        .tolist()
    )

    selected_year = filter_right.selectbox(
        "Election",
        available_years,
        format_func=lambda year: (
            f"{selected_country.title()} {year}"
        ),
        key="holdout_election",
    )

    selected_result = country_elections.loc[
        country_elections["election_year"].astype(int)
        == selected_year
    ].iloc[0]

    selected_predictions = holdout_predictions.loc[
        (
            holdout_predictions["country"]
            == selected_country
        )
        & (
            holdout_predictions["election_year"].astype(int)
            == selected_year
        )
    ].copy()

    selected_election_mae = float(
        selected_predictions["absolute_error"].mean()
    )

    winner_correct = bool(
        int(selected_result["winner_correct"])
    )

    winner_status = (
        "Correct"
        if winner_correct
        else "Miss"
    )

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)

    metric_1.metric(
        "Predicted winner",
        str(selected_result["predicted_winner"]),
    )

    metric_2.metric(
        "Actual winner",
        str(selected_result["actual_winner"]),
    )

    metric_3.metric(
        "Winner result",
        winner_status,
    )

    metric_4.metric(
        "Election MAE",
        f"{selected_election_mae:.2f} pp",
    )

    if winner_correct:
        st.success(
            "The frozen polling-average method selected "
            "the correct election winner."
        )
    else:
        st.warning(
            "This is a retained wrong-winner result. "
            "It remains visible and was not used for retuning."
        )

    comparison_data = selected_predictions[
        [
            "party",
            "selected_vote_prediction",
            "actual_pct",
            "absolute_error",
        ]
    ].melt(
        id_vars=[
            "party",
            "absolute_error",
        ],
        value_vars=[
            "selected_vote_prediction",
            "actual_pct",
        ],
        var_name="measure",
        value_name="vote_share",
    )

    comparison_data["measure"] = comparison_data[
        "measure"
    ].map(
        {
            "selected_vote_prediction": (
                "Final polling average"
            ),
            "actual_pct": "Actual result",
        }
    )

    comparison_figure = px.bar(
        comparison_data,
        x="party",
        y="vote_share",
        color="measure",
        barmode="group",
        text_auto=".2f",
        hover_data={
            "absolute_error": ":.2f",
            "vote_share": ":.2f",
        },
        color_discrete_map={
            "Final polling average": "#4EA1FF",
            "Actual result": "#F2B84B",
        },
    )

    comparison_figure.update_layout(
        xaxis_title="",
        yaxis_title="Vote share (%)",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    )

    st.plotly_chart(
        style_figure(
            comparison_figure,
            (
                f"{selected_country.title()} "
                f"{selected_year}: forecast versus result"
            ),
            height=470,
        ),
        width="stretch",
        config={
            "displaylogo": False,
            "responsive": True,
        },
    )

    chart_left, chart_right = st.columns(2)

    error_detail = selected_predictions[
        [
            "party",
            "vote_share_error",
            "absolute_error",
        ]
    ].copy()

    error_detail["direction"] = error_detail[
        "vote_share_error"
    ].apply(
        lambda value: (
            "Overestimated"
            if value > 0
            else "Underestimated"
        )
    )

    error_detail = error_detail.sort_values(
        "absolute_error",
        ascending=True,
    )

    error_figure = px.bar(
        error_detail,
        x="absolute_error",
        y="party",
        color="direction",
        orientation="h",
        text_auto=".2f",
        hover_data={
            "vote_share_error": ":.2f",
            "absolute_error": ":.2f",
        },
        color_discrete_map={
            "Overestimated": "#F2B84B",
            "Underestimated": "#4EA1FF",
        },
    )

    error_figure.update_layout(
        xaxis_title="Absolute error (percentage points)",
        yaxis_title="",
    )

    with chart_left:
        st.plotly_chart(
            style_figure(
                error_figure,
                "Party-level polling error",
                height=430,
            ),
            width="stretch",
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

    country_error_display = (
        holdout_country_errors
        .sort_values(
            "MAE",
            ascending=False,
        )
        .copy()
    )

    country_error_display["country_label"] = (
        country_error_display["country"]
        .str.title()
    )

    country_figure = px.bar(
        country_error_display,
        x="country_label",
        y="MAE",
        color="country_label",
        text_auto=".2f",
        hover_data={
            "RMSE": ":.2f",
            "mean_error": ":.2f",
            "elections": True,
        },
        color_discrete_sequence=[
            "#F2B84B",
            "#4EA1FF",
            "#32C7C9",
            "#A78BFA",
        ],
    )

    country_figure.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="Mean absolute error (pp)",
    )

    with chart_right:
        st.plotly_chart(
            style_figure(
                country_figure,
                "Holdout error by country",
                height=430,
            ),
            width="stretch",
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

    st.markdown("### All frozen holdout elections")

    displayed_elections = holdout_elections.copy()

    displayed_elections["country"] = (
        displayed_elections["country"]
        .str.title()
    )

    displayed_elections["result"] = (
        displayed_elections["winner_correct"]
        .astype(int)
        .map(
            {
                1: "Correct",
                0: "Miss",
            }
        )
    )

    displayed_elections = displayed_elections[
        [
            "country",
            "election_year",
            "predicted_winner",
            "actual_winner",
            "result",
            "predicted_margin",
            "actual_margin",
        ]
    ].sort_values(
        [
            "country",
            "election_year",
        ]
    )

    displayed_elections = displayed_elections.rename(
        columns={
            "country": "Country",
            "election_year": "Election",
            "predicted_winner": "Predicted winner",
            "actual_winner": "Actual winner",
            "result": "Result",
            "predicted_margin": "Predicted margin",
            "actual_margin": "Actual margin",
        }
    )

    st.dataframe(
        displayed_elections,
        width="stretch",
        hide_index=True,
        column_config={
            "Predicted margin": st.column_config.NumberColumn(
                format="%.2f pp",
            ),
            "Actual margin": st.column_config.NumberColumn(
                format="%.2f pp",
            ),
        },
    )

    st.download_button(
        "Download frozen holdout predictions",
        data=csv_bytes(holdout_predictions),
        file_name="final_holdout_predictions.csv",
        mime="text/csv",
    )
elif selected_section == "Australia 2019 case study":
    st.subheader("Australia 2019: honest failure analysis")

    st.caption(
        "The selected final polling average predicted an ALP two-party-preferred "
        "victory. The actual national two-party-preferred winner was the L/NP. "
        "This failure remains visible because credible evaluation must include "
        "important misses as well as successful predictions."
    )

    case_predictions = holdout_predictions.loc[
        (
            holdout_predictions["country"] == "australia"
        )
        & (
            holdout_predictions["election_year"].astype(int)
            == 2019
        )
    ].copy()

    case_results = holdout_elections.loc[
        (
            holdout_elections["country"] == "australia"
        )
        & (
            holdout_elections["election_year"].astype(int)
            == 2019
        )
    ].copy()

    if case_predictions.empty or case_results.empty:
        st.error(
            "The frozen Australia 2019 holdout artifacts could not be found."
        )
    else:
        case_result = case_results.iloc[0]

        predicted_winner = str(
            case_result["predicted_winner"]
        )

        actual_winner = str(
            case_result["actual_winner"]
        )

        predicted_margin = float(
            case_result["predicted_margin"]
        )

        actual_margin = float(
            case_result["actual_margin"]
        )

        case_mae = float(
            case_predictions["absolute_error"].mean()
        )

        largest_party_error = float(
            case_predictions["absolute_error"].max()
        )

        st.warning(
            "Wrong-winner result retained: the polling average selected "
            f"{predicted_winner}, while the actual winner was "
            f"{actual_winner}. No post-hoc retuning was performed."
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Predicted winner",
            predicted_winner,
        )

        c2.metric(
            "Actual winner",
            actual_winner,
        )

        c3.metric(
            "Predicted margin",
            f"{predicted_margin:.2f} pp",
        )

        c4.metric(
            "Actual margin",
            f"{actual_margin:.2f} pp",
        )

        c5.metric(
            "Election MAE",
            f"{case_mae:.2f} pp",
        )

        case_long = case_predictions[
            [
                "party",
                "selected_vote_prediction",
                "actual_pct",
                "vote_share_error",
                "absolute_error",
            ]
        ].melt(
            id_vars=[
                "party",
                "vote_share_error",
                "absolute_error",
            ],
            value_vars=[
                "selected_vote_prediction",
                "actual_pct",
            ],
            var_name="measure",
            value_name="vote_share",
        )

        case_long["measure"] = case_long["measure"].map(
            {
                "selected_vote_prediction": "Final polling average",
                "actual_pct": "Actual result",
            }
        )

        comparison_figure = px.bar(
            case_long,
            x="party",
            y="vote_share",
            color="measure",
            barmode="group",
            text_auto=".2f",
            hover_data={
                "vote_share_error": ":.2f",
                "absolute_error": ":.2f",
                "vote_share": ":.2f",
            },
            color_discrete_map={
                "Final polling average": "#4EA1FF",
                "Actual result": "#F2B84B",
            },
        )

        comparison_figure.update_layout(
            xaxis_title="",
            yaxis_title="Two-party-preferred vote (%)",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )

        st.plotly_chart(
            style_figure(
                comparison_figure,
                "Australia 2019: polling average versus actual result",
                height=470,
            ),
            width="stretch",
            config={
                "displaylogo": False,
                "responsive": True,
            },
        )

        analysis_left, analysis_right = st.columns(2)

        margin_data = pd.DataFrame(
            {
                "Measure": [
                    "Predicted margin",
                    "Actual margin",
                ],
                "Margin": [
                    predicted_margin,
                    actual_margin,
                ],
                "Winner": [
                    predicted_winner,
                    actual_winner,
                ],
            }
        )

        margin_figure = px.bar(
            margin_data,
            x="Measure",
            y="Margin",
            color="Winner",
            text_auto=".2f",
            hover_data={
                "Margin": ":.2f",
                "Winner": True,
            },
            color_discrete_sequence=[
                "#4EA1FF",
                "#F2B84B",
            ],
        )

        margin_figure.update_layout(
            showlegend=True,
            xaxis_title="",
            yaxis_title="Winning margin (pp)",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )

        with analysis_left:
            st.plotly_chart(
                style_figure(
                    margin_figure,
                    "Winner and margin reversal",
                    height=420,
                ),
                width="stretch",
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
            )

        party_error_data = case_predictions[
            [
                "party",
                "vote_share_error",
                "absolute_error",
            ]
        ].copy()

        party_error_data["Error direction"] = (
            party_error_data["vote_share_error"].apply(
                lambda value: (
                    "Overestimated"
                    if value > 0
                    else "Underestimated"
                )
            )
        )

        error_figure = px.bar(
            party_error_data,
            x="party",
            y="absolute_error",
            color="Error direction",
            text_auto=".2f",
            hover_data={
                "vote_share_error": ":.2f",
                "absolute_error": ":.2f",
            },
            color_discrete_map={
                "Overestimated": "#F2B84B",
                "Underestimated": "#4EA1FF",
            },
        )

        error_figure.update_layout(
            xaxis_title="",
            yaxis_title="Absolute error (pp)",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )

        with analysis_right:
            st.plotly_chart(
                style_figure(
                    error_figure,
                    "Party-level forecast error",
                    height=420,
                ),
                width="stretch",
                config={
                    "displaylogo": False,
                    "responsive": True,
                },
            )

        interpretation_left, interpretation_right = st.columns(2)

        with interpretation_left:
            with st.container(border=True):
                st.markdown("### What the frozen result shows")

                st.markdown(
                    f"""
                    - The polling average placed **{predicted_winner}**
                      ahead by **{predicted_margin:.2f} percentage points**.
                    - The actual result placed **{actual_winner}**
                      ahead by **{actual_margin:.2f} percentage points**.
                    - Mean party-level absolute error was
                      **{case_mae:.2f} percentage points**.
                    - The largest party-level miss was
                      **{largest_party_error:.2f} percentage points**.
                    - The direction of the polling lead was therefore reversed.
                    """
                )

        with interpretation_right:
            with st.container(border=True):
                st.markdown("### What this analysis does not claim")

                st.markdown(
                    """
                    - It does not identify a single causal explanation for the miss.
                    - It does not estimate seat outcomes or government formation.
                    - It does not prove that the same error pattern will recur.
                    - It does not use the result to modify the selected method.
                    - It remains a descriptive audit of the frozen evaluation.
                    """
                )

        st.markdown("### Frozen party-level evidence")

        case_table = case_predictions[
            [
                "party",
                "selected_vote_prediction",
                "actual_pct",
                "vote_share_error",
                "absolute_error",
                "selected_model_predicted_winner",
            ]
        ].copy()

        case_table["selected_model_predicted_winner"] = (
            case_table["selected_model_predicted_winner"]
            .astype(int)
            .map(
                {
                    1: "Yes",
                    0: "No",
                }
            )
        )

        case_table = case_table.rename(
            columns={
                "party": "Party",
                "selected_vote_prediction": "Polling average",
                "actual_pct": "Actual result",
                "vote_share_error": "Signed error",
                "absolute_error": "Absolute error",
                "selected_model_predicted_winner": "Predicted winner",
            }
        )

        st.dataframe(
            case_table,
            width="stretch",
            hide_index=True,
            column_config={
                "Polling average": st.column_config.NumberColumn(
                    format="%.2f%%",
                ),
                "Actual result": st.column_config.NumberColumn(
                    format="%.2f%%",
                ),
                "Signed error": st.column_config.NumberColumn(
                    format="%+.2f pp",
                ),
                "Absolute error": st.column_config.NumberColumn(
                    format="%.2f pp",
                ),
            },
        )

        st.info(
            "The Australia 2019 result is included as a central limitation "
            "and an example of why aggregate vote-share accuracy and correct "
            "winner classification must be evaluated separately."
        )


elif selected_section == "Methodology and governance":
    st.subheader("Model-selection decision")

    st.markdown(
        f"**Selected model:** `{selected_model}`"
    )

    st.markdown(
        f"**Prediction column:** "
        f"`{selection_decision['prediction_column']}`"
    )

    st.markdown(
        f"**Selection basis:** "
        f"{selection_decision['selection_basis']}"
    )

    st.markdown(
        f"**Challenger decision:** "
        f"{selection_decision['challenger_decision']}"
    )

    st.markdown(
        f"**Holdout usage:** "
        f"{selection_decision['holdout_usage']}"
    )

    left, right = st.columns(2)

    with left:
        with st.container(border=True):
            st.markdown("### Validation design")

            st.markdown(
                """
                - Elections, not individual rows, are the validation unit.
                - Fourteen elections form the development set.
                - Eight later elections form the chronological holdout.
                - Leave-one-election-out validation governs model selection.
                - The final holdout was evaluated once and then locked.
                """
            )

    with right:
        with st.container(border=True):
            st.markdown("### Leakage controls")

            st.markdown(
                """
                - Post-election polls are excluded.
                - Election-result marker rows are not treated as polls.
                - Holdout labels are not used for model selection.
                - The dashboard performs no retraining.
                - Frozen outputs remain the source of displayed results.
                """
            )

    st.info(
        "This project is a historical analytical and methodological "
        "demonstration. It is not a live election forecast, a seat model, "
        "or a recommendation about electoral outcomes."
    )
