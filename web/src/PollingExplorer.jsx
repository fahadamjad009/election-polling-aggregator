import { useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'

const layout = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#969696' },
  margin: { l: 55, r: 25, t: 25, b: 65 },
}

function PollingExplorer() {
  const [trajectory, setTrajectory] = useState([])
  const [partyErrors, setPartyErrors] = useState([])
  const [country, setCountry] = useState('')
  const [year, setYear] = useState('')
  const [party, setParty] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      fetch(`${import.meta.env.BASE_URL}data/polling-trajectory.json`).then((response) =>
        response.json(),
      ),
      fetch(`${import.meta.env.BASE_URL}data/party-errors.json`).then((response) =>
        response.json(),
      ),
    ])
      .then(([trajectoryData, errorData]) => {
        setTrajectory(trajectoryData)
        setPartyErrors(errorData)
      })
      .catch(() => setError('Unable to load polling history.'))
  }, [])

  const countries = useMemo(
    () =>
      [...new Set(trajectory.map((row) => row.country_label))].sort(),
    [trajectory],
  )

  const selectedCountry = country || countries[0] || ''

  const years = useMemo(
    () =>
      [
        ...new Set(
          trajectory
            .filter((row) => row.country_label === selectedCountry)
            .map((row) => Number(row.election_year)),
        ),
      ].sort((a, b) => a - b),
    [trajectory, selectedCountry],
  )

  const selectedYear = years.includes(Number(year))
    ? Number(year)
    : years[0]

  const parties = useMemo(
    () =>
      [
        ...new Set(
          trajectory
            .filter(
              (row) =>
                row.country_label === selectedCountry &&
                Number(row.election_year) === selectedYear,
            )
            .map((row) => row.party),
        ),
      ].sort(),
    [trajectory, selectedCountry, selectedYear],
  )

  const selectedParty = parties.includes(party)
    ? party
    : parties[0] || ''

  const selectedTrajectory = useMemo(
    () =>
      trajectory
        .filter(
          (row) =>
            row.country_label === selectedCountry &&
            Number(row.election_year) === selectedYear &&
            row.party === selectedParty,
        )
        .sort(
          (a, b) =>
            new Date(a.poll_date).getTime() -
            new Date(b.poll_date).getTime(),
        ),
    [trajectory, selectedCountry, selectedYear, selectedParty],
  )

  const countryErrors = partyErrors.filter(
    (row) => row.country_label === selectedCountry,
  )

  const maxCountryError = Math.max(
    ...countryErrors.map((row) => Number(row.absolute_error)),
    1,
  )

  if (error) {
    return <p className="dataError">{error}</p>
  }

  return (
    <section className="analyticsSection" id="polling-history">
      <div className="sectionHeading">
        <p className="eyebrow">Historical dynamics</p>
        <h2>Polling trajectories and error distributions.</h2>
      </div>

      <div className="filterRow">
        <label>
          Country
          <select
            value={selectedCountry}
            onChange={(event) => {
              setCountry(event.target.value)
              setYear('')
              setParty('')
            }}
          >
            {countries.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>

        <label>
          Election
          <select
            value={selectedYear || ''}
            onChange={(event) => {
              setYear(event.target.value)
              setParty('')
            }}
          >
            {years.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>

        <label>
          Party
          <select
            value={selectedParty}
            onChange={(event) => setParty(event.target.value)}
          >
            {parties.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="chartGrid">
        <article className="chartCard">
          <div className="chartHeading">
            <h3>
              {selectedCountry} {selectedYear}: {selectedParty}
            </h3>
            <p>Individual polls and the rolling polling average.</p>
          </div>

          <Plot
            data={[
              {
                type: 'scatter',
                mode: 'markers',
                name: 'Poll observations',
                x: selectedTrajectory.map((row) => row.poll_date),
                y: selectedTrajectory.map((row) => Number(row.pct)),
                marker: {
                  size: 6,
                  opacity: 0.35,
                  color: '#969696',
                },
                hovertemplate:
                  '%{x}<br>Poll: %{y:.1f}%<extra></extra>',
              },
              {
                type: 'scatter',
                mode: 'lines',
                name: 'Rolling average',
                x: selectedTrajectory.map((row) => row.poll_date),
                y: selectedTrajectory.map((row) =>
                  Number(row.rolling_avg),
                ),
                line: {
                  width: 3,
                  color: '#b6ff3b',
                },
                hovertemplate:
                  '%{x}<br>Average: %{y:.1f}%<extra></extra>',
              },
            ]}
            layout={{
              ...layout,
              height: 470,
              xaxis: {
                title: 'Polling date',
                gridcolor: '#242424',
              },
              yaxis: {
                title: 'Polling support (%)',
                gridcolor: '#242424',
              },
              legend: {
                orientation: 'h',
                x: 0.5,
                xanchor: 'center',
                y: -0.25,
              },
            }}
            config={{ responsive: true, displaylogo: false }}
            useResizeHandler
            className="plot"
          />
        </article>

        <article className="chartCard">
          <div className="chartHeading">
            <h3>{selectedCountry} polling-error distribution</h3>
            <p>
              Party-level absolute error across development and holdout
              elections.
            </p>
          </div>

          <Plot
            data={['Development', 'Holdout'].map((split) => ({
              type: 'violin',
              name: split,
              y: countryErrors
                .filter((row) => row.evaluation_split === split)
                .map((row) => Number(row.absolute_error)),
              box: { visible: true },
              meanline: { visible: true },
              points: 'all',
              spanmode: 'hard',
              scalemode: 'width',
              jitter: 0.15,
              pointpos: 0,
              hovertemplate:
                `${split}<br>Error: %{y:.2f} pp<extra></extra>`,
            }))}
            layout={{
              ...layout,
              height: 470,
              violinmode: 'group',
              xaxis: {
                title: '',
              },
              yaxis: {
                title: 'Absolute polling error (percentage points)',
                range: [0, maxCountryError * 1.15],
                gridcolor: '#242424',
              },
              showlegend: false,
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

export default PollingExplorer

