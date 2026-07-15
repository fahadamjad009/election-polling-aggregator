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
  margin: { l: 65, r: 25, t: 25, b: 70 },
}

function HoldoutEvidence() {
  const [partyErrors, setPartyErrors] = useState([])
  const [holdoutResults, setHoldoutResults] = useState([])

  useEffect(() => {
    Promise.all([
      fetch(`${import.meta.env.BASE_URL}data/party-errors.json`).then((response) => response.json()),
      fetch(`${import.meta.env.BASE_URL}data/holdout-election-results.json`).then((response) =>
        response.json(),
      ),
    ]).then(([errorData, resultData]) => {
      setPartyErrors(errorData)
      setHoldoutResults(resultData)
    })
  }, [])

  const maxError = useMemo(
    () =>
      Math.max(
        ...partyErrors.map((row) => Number(row.absolute_error)),
        1,
      ),
    [partyErrors],
  )

  const electionLabels = holdoutResults.map(
    (row) =>
      `${countryNames[row.country] ?? row.country} ${row.election_year}`,
  )

  const australia2019 = holdoutResults.find(
    (row) =>
      row.country === 'australia' &&
      Number(row.election_year) === 2019,
  )

  return (
    <section className="analyticsSection" id="holdout-evidence">
      <div className="sectionHeading">
        <p className="eyebrow">Frozen holdout evidence</p>
        <h2>Evidence density, margins and retained failure.</h2>
      </div>

      <div className="chartGrid">
        <article className="chartCard">
          <div className="chartHeading">
            <h3>Polling volume versus absolute error</h3>
            <p>
              Each point represents one evaluated party-election result.
            </p>
          </div>

          <Plot
            data={['Development', 'Holdout'].map((split) => {
              const rows = partyErrors.filter(
                (row) => row.evaluation_split === split,
              )

              return {
                type: 'scatter',
                mode: 'markers',
                name: split,
                x: rows.map((row) =>
                  Number(row.n_poll_observations),
                ),
                y: rows.map((row) => Number(row.absolute_error)),
                text: rows.map(
                  (row) =>
                    `${row.election_label}<br>${row.party}<br>` +
                    `${row.n_poll_observations} observations`,
                ),
                hovertemplate:
                  '%{text}<br>Absolute error: %{y:.2f} pp<extra></extra>',
                marker: {
                  size: split === 'Holdout' ? 12 : 9,
                  opacity: 0.78,
                  color:
                    split === 'Holdout' ? '#b6ff3b' : '#777777',
                  line: {
                    color: '#050505',
                    width: 1,
                  },
                },
              }
            })}
            layout={{
              ...layout,
              height: 470,
              xaxis: {
                title: 'Poll observations',
                gridcolor: '#242424',
                rangemode: 'tozero',
              },
              yaxis: {
                title: 'Absolute error (percentage points)',
                gridcolor: '#242424',
                range: [0, maxError * 1.12],
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
            <h3>Predicted versus actual winning margin</h3>
            <p>
              Comparison across the eight chronological holdout elections.
            </p>
          </div>

          <Plot
            data={[
              {
                type: 'bar',
                name: 'Predicted margin',
                orientation: 'h',
                y: electionLabels,
                x: holdoutResults.map((row) =>
                  Number(row.predicted_margin),
                ),
                hovertemplate:
                  '%{y}<br>Predicted margin: %{x:.2f} pp<extra></extra>',
              },
              {
                type: 'bar',
                name: 'Actual margin',
                orientation: 'h',
                y: electionLabels,
                x: holdoutResults.map((row) =>
                  Number(row.actual_margin),
                ),
                hovertemplate:
                  '%{y}<br>Actual margin: %{x:.2f} pp<extra></extra>',
              },
            ]}
            layout={{
              ...layout,
              height: 470,
              barmode: 'group',
              xaxis: {
                title: 'Winning margin (percentage points)',
                gridcolor: '#242424',
                rangemode: 'tozero',
              },
              yaxis: {
                automargin: true,
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
      </div>

      {australia2019 && (
        <article className="failureCard">
          <div>
            <p className="eyebrow">Retained failure case</p>
            <h3>Australia 2019 remained a wrong-winner prediction.</h3>
          </div>

          <div className="failureMetrics">
            <span>
              Predicted
              <strong>{australia2019.predicted_winner}</strong>
            </span>

            <span>
              Actual
              <strong>{australia2019.actual_winner}</strong>
            </span>

            <span>
              Predicted margin
              <strong>
                {Number(australia2019.predicted_margin).toFixed(2)} pp
              </strong>
            </span>

            <span>
              Actual margin
              <strong>
                {Number(australia2019.actual_margin).toFixed(2)} pp
              </strong>
            </span>
          </div>
        </article>
      )}
    </section>
  )
}

export default HoldoutEvidence
