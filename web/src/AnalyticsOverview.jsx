import { useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'

const chartLayout = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#969696' },
  margin: { l: 45, r: 25, t: 30, b: 55 },
}

function AnalyticsOverview() {
  const [countries, setCountries] = useState([])
  const [elections, setElections] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      fetch(`${import.meta.env.BASE_URL}data/country-performance.json`).then((response) => response.json()),
      fetch(`${import.meta.env.BASE_URL}data/election-errors.json`).then((response) => response.json()),
    ])
      .then(([countryData, electionData]) => {
        setCountries(countryData)
        setElections(electionData)
      })
      .catch(() => setError('Unable to load analytical data.'))
  }, [])

  const heatmap = useMemo(() => {
    const years = [...new Set(elections.map((row) => row.election_year))]
      .sort((a, b) => a - b)

    const countryNames = [
      ...new Set(elections.map((row) => row.country_label)),
    ]

    const values = countryNames.map((country) =>
      years.map((year) => {
        const row = elections.find(
          (item) =>
            item.country_label === country &&
            item.election_year === year,
        )

        return row ? Number(row.election_mae) : null
      }),
    )

    const labels = countryNames.map((country) =>
      years.map((year) => {
        const row = elections.find(
          (item) =>
            item.country_label === country &&
            item.election_year === year,
        )

        if (!row) return ''

        return [
          `${country} ${year}`,
          `MAE: ${Number(row.election_mae).toFixed(2)} pp`,
          row.result_status,
        ].join('<br>')
      }),
    )

    return { years, countryNames, values, labels }
  }, [elections])

  if (error) {
    return <p className="dataError">{error}</p>
  }

  return (
    <section className="analyticsSection" id="analytics">
      <div className="sectionHeading">
        <p className="eyebrow">Interactive evidence</p>
        <h2>Cross-country polling performance.</h2>
      </div>

      <div className="chartGrid">
        <article className="chartCard">
          <div className="chartHeading">
            <h3>Geographic performance</h3>
            <p>Bubble size reflects polling evidence volume.</p>
          </div>

          <Plot
            data={[
              {
                type: 'scattergeo',
                locations: countries.map((row) => row.iso_alpha),
                text: countries.map(
                  (row) =>
                    `${row.country_label}<br>` +
                    `${Number(row.poll_observations).toLocaleString()} polls<br>` +
                    `${(Number(row.winner_accuracy) * 100).toFixed(1)}% winner accuracy`,
                ),
                hovertemplate: '%{text}<extra></extra>',
                marker: {
                  size: countries.map(
                    (row) =>
                      12 +
                      Math.sqrt(Number(row.poll_observations)) / 3,
                  ),
                  color: countries.map((row) =>
                    Number(row.winner_accuracy),
                  ),
                  colorscale: 'Viridis',
                  cmin: 0.75,
                  cmax: 1,
                  line: { color: '#050505', width: 1 },
                  colorbar: {
                    title: 'Accuracy',
                    tickformat: '.0%',
                    thickness: 10,
                  },
                },
              },
            ]}
            layout={{
              ...chartLayout,
              geo: {
                bgcolor: 'transparent',
                projection: { type: 'natural earth' },
                showland: true,
                landcolor: '#171717',
                showocean: true,
                oceancolor: '#080808',
                showcountries: true,
                countrycolor: '#303030',
              },
              height: 470,
            }}
            config={{ responsive: true, displaylogo: false }}
            useResizeHandler
            className="plot"
          />
        </article>

        <article className="chartCard">
          <div className="chartHeading">
            <h3>Election-level error matrix</h3>
            <p>Mean absolute error by election and country.</p>
          </div>

          <Plot
            data={[
              {
                type: 'heatmap',
                x: heatmap.years,
                y: heatmap.countryNames,
                z: heatmap.values,
                text: heatmap.labels,
                hovertemplate: '%{text}<extra></extra>',
                colorscale: 'Viridis',
                colorbar: {
                  title: 'MAE',
                  ticksuffix: ' pp',
                  thickness: 10,
                },
                xgap: 3,
                ygap: 3,
              },
            ]}
            layout={{
              ...chartLayout,
              height: 470,
              xaxis: {
                title: 'Election year',
                gridcolor: '#222222',
              },
              yaxis: {
                automargin: true,
                gridcolor: '#222222',
              },
            }}
            config={{ responsive: true, displaylogo: false }}
            useResizeHandler
            className="plot"
          />
        </article>
      </div>
    </section>
  )
}

export default AnalyticsOverview
