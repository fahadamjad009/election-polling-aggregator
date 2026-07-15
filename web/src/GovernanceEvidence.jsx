import { useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'

const countryNames = {
  australia: 'Australia',
  canada: 'Canada',
  uk: 'United Kingdom',
  us: 'United States',
}

const layout = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#969696' },
  margin: { l: 60, r: 25, t: 25, b: 70 },
}

function GovernanceEvidence() {
  const [audit, setAudit] = useState([])
  const [metrics, setMetrics] = useState([])
  const [selection, setSelection] = useState(null)

  useEffect(() => {
    Promise.all([
      fetch(`${import.meta.env.BASE_URL}data/model-dataset-audit.json`).then((response) =>
        response.json(),
      ),
      fetch(`${import.meta.env.BASE_URL}data/holdout-metrics.json`).then((response) =>
        response.json(),
      ),
      fetch(`${import.meta.env.BASE_URL}data/model-selection.json`).then((response) =>
        response.json(),
      ),
    ]).then(([auditData, metricData, selectionData]) => {
      setAudit(auditData)
      setMetrics(metricData)
      setSelection(selectionData)
    })
  }, [])

  const countryTotals = useMemo(() => {
    const totals = {}

    audit.forEach((row) => {
      if (!totals[row.country]) {
        totals[row.country] = {
          country: row.country,
          sourceRows: 0,
          modelRows: 0,
        }
      }

      totals[row.country].sourceRows += Number(row.source_feature_rows)
      totals[row.country].modelRows += Number(row.model_party_rows)
    })

    return Object.values(totals)
  }, [audit])

  const splitMatrix = useMemo(() => {
    const years = [
      ...new Set(audit.map((row) => Number(row.election_year))),
    ].sort((a, b) => a - b)

    const countries = [
      ...new Set(audit.map((row) => row.country)),
    ]

    const values = countries.map((country) =>
      years.map((year) => {
        const row = audit.find(
          (item) =>
            item.country === country &&
            Number(item.election_year) === year,
        )

        if (!row) return null

        return row.dataset_split === 'holdout' ? 1 : 0
      }),
    )

    const labels = countries.map((country) =>
      years.map((year) => {
        const row = audit.find(
          (item) =>
            item.country === country &&
            Number(item.election_year) === year,
        )

        if (!row) return ''

        return (
          `${countryNames[country] ?? country} ${year}<br>` +
          `${row.dataset_split}<br>` +
          `${row.source_feature_rows} source rows<br>` +
          `${row.model_party_rows} model rows<br>` +
          `${row.post_election_rows} post-election rows`
        )
      }),
    )

    return { years, countries, values, labels }
  }, [audit])

  const metricValue = (name) =>
    Number(metrics.find((row) => row.metric === name)?.value ?? 0)

  return (
    <section className="analyticsSection" id="governance">
      <div className="sectionHeading">
        <p className="eyebrow">Reproducibility and governance</p>
        <h2>Leakage controls and model-selection evidence.</h2>
      </div>

      <div className="chartGrid">
        <article className="chartCard">
          <div className="chartHeading">
            <h3>Feature rows versus model rows</h3>
            <p>
              National polling evidence is reduced to auditable
              party-election model records.
            </p>
          </div>

          <Plot
            data={[
              {
                type: 'bar',
                name: 'Source feature rows',
                x: countryTotals.map(
                  (row) => countryNames[row.country] ?? row.country,
                ),
                y: countryTotals.map((row) => row.sourceRows),
                hovertemplate:
                  '%{x}<br>Source rows: %{y:,}<extra></extra>',
              },
              {
                type: 'bar',
                name: 'Model party rows',
                x: countryTotals.map(
                  (row) => countryNames[row.country] ?? row.country,
                ),
                y: countryTotals.map((row) => row.modelRows),
                hovertemplate:
                  '%{x}<br>Model rows: %{y:,}<extra></extra>',
              },
            ]}
            layout={{
              ...layout,
              height: 470,
              barmode: 'group',
              yaxis: {
                title: 'Rows (log scale)',
                type: 'log',
                tickvals: [10, 100, 1000, 5000],
                ticktext: ['10', '100', '1k', '5k'],
                gridcolor: '#242424',
              },
              legend: {
                orientation: 'h',
                x: 0.5,
                xanchor: 'center',
                y: -0.24,
              },
            }}
            config={{ responsive: true, displaylogo: false }}
            useResizeHandler
            className="plot"
          />
        </article>

        <article className="chartCard">
          <div className="chartHeading">
            <h3>Chronological split audit</h3>
            <p>
              Grey represents development elections and green represents
              holdout elections. Zero post-election rows were retained.
            </p>
          </div>

          <Plot
            data={[
              {
                type: 'heatmap',
                x: splitMatrix.years,
                y: splitMatrix.countries.map(
                  (country) => countryNames[country] ?? country,
                ),
                z: splitMatrix.values,
                text: splitMatrix.labels,
                hovertemplate: '%{text}<extra></extra>',
                zmin: 0,
                zmax: 1,
                colorscale: [
                  [0, '#3b3b3b'],
                  [0.49, '#3b3b3b'],
                  [0.5, '#b6ff3b'],
                  [1, '#b6ff3b'],
                ],
                showscale: false,
                xgap: 3,
                ygap: 3,
              },
            ]}
            layout={{
              ...layout,
              height: 470,
              xaxis: {
                title: 'Election year',
                tickangle: -45,
                tickfont: { size: 10 },
              },
              yaxis: {
                automargin: true,
              },
            }}
            config={{ responsive: true, displaylogo: false }}
            useResizeHandler
            className="plot"
          />
        </article>
      </div>

      <div className="governanceStats">
        <article>
          <span>Selected method</span>
          <strong>
            {selection?.selected_model?.replaceAll('_', ' ') ?? '—'}
          </strong>
        </article>

        <article>
          <span>Holdout MAE</span>
          <strong>{metricValue('MAE').toFixed(2)} pp</strong>
        </article>

        <article>
          <span>Holdout RMSE</span>
          <strong>{metricValue('RMSE').toFixed(2)} pp</strong>
        </article>

        <article>
          <span>Winner accuracy</span>
          <strong>
            {(metricValue('election_winner_accuracy') * 100).toFixed(1)}%
          </strong>
        </article>
      </div>
    </section>
  )
}

export default GovernanceEvidence
