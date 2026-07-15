import { useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'

const countryLabels = {
  australia: 'Australia',
  canada: 'Canada',
  uk: 'United Kingdom',
  us: 'United States',
}

const chartLayout = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#969696' },
  margin: { l: 55, r: 25, t: 25, b: 65 },
}

function ModelEvidence() {
  const [ablation, setAblation] = useState([])
  const [countryErrors, setCountryErrors] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      fetch('/data/feature-ablation.json').then((response) =>
        response.json(),
      ),
      fetch('/data/holdout-country-errors.json').then((response) =>
        response.json(),
      ),
    ])
      .then(([ablationData, countryData]) => {
        setAblation(ablationData)
        setCountryErrors(countryData)
      })
      .catch(() => setError('Unable to load model evidence.'))
  }, [])

  const regressionHeatmap = useMemo(() => {
    const regressionRows = ablation.filter(
      (row) =>
        row.task === 'vote_share_regression' &&
        ['MAE', 'RMSE'].includes(row.metric),
    )

    const configurations = [
      ...new Set(
        regressionRows.map(
          (row) =>
            `${row.feature_set} · ${row.model.replaceAll('_', ' ')}`,
        ),
      ),
    ]

    const metrics = ['MAE', 'RMSE']

    const values = configurations.map((configuration) =>
      metrics.map((metric) => {
        const row = regressionRows.find(
          (item) =>
            `${item.feature_set} · ${item.model.replaceAll('_', ' ')}` ===
              configuration && item.metric === metric,
        )

        return row ? Number(row.value) : null
      }),
    )

    const labels = configurations.map((configuration) =>
      metrics.map((metric) => {
        const row = regressionRows.find(
          (item) =>
            `${item.feature_set} · ${item.model.replaceAll('_', ' ')}` ===
              configuration && item.metric === metric,
        )

        return row
          ? `${configuration}<br>${metric}: ${Number(row.value).toFixed(3)}`
          : ''
      }),
    )

    return {
      configurations,
      metrics,
      values,
      labels,
    }
  }, [ablation])

  if (error) {
    return <p className="dataError">{error}</p>
  }

  return (
    <section className="analyticsSection" id="model-evidence">
      <div className="sectionHeading">
        <p className="eyebrow">Model evidence</p>
        <h2>Benchmark selection and holdout performance.</h2>
      </div>

      <div className="chartGrid">
        <article className="chartCard">
          <div className="chartHeading">
            <h3>Development feature ablation</h3>
            <p>
              Lower regression error is better. The polling-average
              benchmark remains the selected method.
            </p>
          </div>

          <Plot
            data={[
              {
                type: 'heatmap',
                x: regressionHeatmap.metrics,
                y: regressionHeatmap.configurations,
                z: regressionHeatmap.values,
                text: regressionHeatmap.labels,
                hovertemplate: '%{text}<extra></extra>',
                colorscale: 'Viridis',
                reversescale: true,
                xgap: 4,
                ygap: 4,
                colorbar: {
                  title: 'Error',
                  ticksuffix: ' pp',
                  thickness: 10,
                },
              },
            ]}
            layout={{
              ...chartLayout,
              height: 470,
              xaxis: {
                title: 'Development metric',
                side: 'bottom',
              },
              yaxis: {
                automargin: true,
                tickfont: { size: 11 },
              },
            }}
            config={{
              responsive: true,
              displaylogo: false,
            }}
            useResizeHandler
            className="plot"
          />
        </article>

        <article className="chartCard">
          <div className="chartHeading">
            <h3>Chronological holdout by country</h3>
            <p>
              Final MAE and RMSE after model selection was frozen.
            </p>
          </div>

          <Plot
            data={[
              {
                type: 'bar',
                name: 'MAE',
                x: countryErrors.map(
                  (row) => countryLabels[row.country] ?? row.country,
                ),
                y: countryErrors.map((row) => Number(row.MAE)),
                hovertemplate:
                  '%{x}<br>MAE: %{y:.2f} pp<extra></extra>',
              },
              {
                type: 'bar',
                name: 'RMSE',
                x: countryErrors.map(
                  (row) => countryLabels[row.country] ?? row.country,
                ),
                y: countryErrors.map((row) => Number(row.RMSE)),
                hovertemplate:
                  '%{x}<br>RMSE: %{y:.2f} pp<extra></extra>',
              },
            ]}
            layout={{
              ...chartLayout,
              height: 470,
              barmode: 'group',
              xaxis: {
                title: '',
                tickangle: -18,
              },
              yaxis: {
                title: 'Polling error (percentage points)',
                rangemode: 'tozero',
                gridcolor: '#242424',
              },
              legend: {
                orientation: 'h',
                x: 0.5,
                xanchor: 'center',
                y: -0.24,
              },
            }}
            config={{
              responsive: true,
              displaylogo: false,
            }}
            useResizeHandler
            className="plot"
          />
        </article>
      </div>
    </section>
  )
}

export default ModelEvidence
