import { useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'

const layout = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#969696' },
  margin: { l: 25, r: 25, t: 25, b: 35 },
}

function ScopeAudit() {
  const [included, setIncluded] = useState([])
  const [excluded, setExcluded] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      fetch('/data/scope-included.json').then((response) =>
        response.json(),
      ),
      fetch('/data/scope-excluded.json').then((response) =>
        response.json(),
      ),
    ])
      .then(([includedData, excludedData]) => {
        setIncluded(includedData)
        setExcluded(excludedData)
      })
      .catch(() => setError('Unable to load polling-scope audit.'))
  }, [])

  const exclusionReasons = useMemo(() => {
    const totals = {}

    excluded.forEach((row) => {
      const reason =
        row.effective_scope_reason || 'Other reviewed table'

      if (!totals[reason]) {
        totals[reason] = {
          tables: 0,
          rows: 0,
        }
      }

      totals[reason].tables += 1
      totals[reason].rows += Number(row.poll_party_rows || 0)
    })

    return Object.entries(totals)
      .map(([reason, values]) => ({
        reason,
        ...values,
      }))
      .sort((a, b) => b.tables - a.tables)
  }, [excluded])

  if (error) {
    return <p className="dataError">{error}</p>
  }

  return (
    <section className="analyticsSection" id="scope-audit">
      <div className="sectionHeading">
        <p className="eyebrow">Polling-scope governance</p>
        <h2>National evidence was selected deliberately.</h2>
      </div>

      <div className="chartGrid">
        <article className="chartCard">
          <div className="chartHeading">
            <h3>Source-table inclusion</h3>
            <p>
              Audited source tables retained or excluded from national
              polling features.
            </p>
          </div>

          <Plot
            data={[
              {
                type: 'pie',
                labels: ['Included', 'Excluded'],
                values: [included.length, excluded.length],
                hole: 0.64,
                textinfo: 'label+value',
                hovertemplate:
                  '%{label}<br>%{value} tables<br>%{percent}<extra></extra>',
                marker: {
                  colors: ['#b6ff3b', '#323232'],
                  line: {
                    color: '#101010',
                    width: 2,
                  },
                },
              },
            ]}
            layout={{
              ...layout,
              height: 470,
              showlegend: false,
              annotations: [
                {
                  text: `${included.length + excluded.length}<br>audited`,
                  x: 0.5,
                  y: 0.5,
                  showarrow: false,
                  font: {
                    color: '#f7f7f7',
                    size: 20,
                  },
                },
              ],
            }}
            config={{ responsive: true, displaylogo: false }}
            useResizeHandler
            className="plot"
          />
        </article>

        <article className="chartCard">
          <div className="chartHeading">
            <h3>Why tables were excluded</h3>
            <p>
              Area represents the number of source tables associated
              with each audit reason.
            </p>
          </div>

          <Plot
            data={[
              {
                type: 'treemap',
                labels: exclusionReasons.map((row) =>
                  row.reason.length > 30
                    ? `${row.reason.slice(0, 30)}?`
                    : row.reason,
                ),
                customdata: exclusionReasons.map((row) => row.reason),
                parents: exclusionReasons.map(() => ''),
                values: exclusionReasons.map((row) => row.tables),
                text: exclusionReasons.map(
                  (row) =>
                    `${row.tables} tables<br>` +
                    `${row.rows.toLocaleString()} poll-party rows`,
                ),
                textinfo: 'label+value',
                textfont: { size: 11 },
                tiling: {
                  packing: 'squarify',
                  pad: 3,
                },
                hovertemplate:
                  '%{customdata}<br>%{text}<extra></extra>',
                marker: {
                  colorscale: 'Viridis',
                  colors: exclusionReasons.map((row) => row.tables),
                  line: {
                    color: '#101010',
                    width: 2,
                  },
                },
              },
            ]}
            layout={{
              ...layout,
              height: 470,
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

export default ScopeAudit
