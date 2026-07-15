import './App.css'
import SectionNav from './SectionNav'
import AnalyticsOverview from './AnalyticsOverview'
import ModelEvidence from './ModelEvidence'
import PollingExplorer from './PollingExplorer'
import ScopeAudit from './ScopeAudit'
import HoldoutEvidence from './HoldoutEvidence'
import GovernanceEvidence from './GovernanceEvidence'

const liveAppUrl =
  'https://election-polling-aggregator.streamlit.app'

const repositoryUrl =
  'https://github.com/fahadamjad009/election-polling-aggregator'

const metrics = [
  {
    value: '4',
    label: 'Countries',
    detail: 'Australia, Canada, United Kingdom and United States',
  },
  {
    value: '22',
    label: 'Elections',
    detail: 'Development and chronological holdout coverage',
  },
  {
    value: '1.24',
    label: 'Holdout MAE',
    detail: 'Percentage-point error on the frozen holdout',
  },
  {
    value: '87.5%',
    label: 'Winner accuracy',
    detail: 'Final chronological holdout performance',
  },
]

const evidence = [
  {
    number: '01',
    title: 'Chronological validation',
    text: 'Election splits preserve time order and keep the final holdout isolated from model selection.',
  },
  {
    number: '02',
    title: 'Reproducible evidence',
    text: 'Versioned datasets, deterministic builders, automated tests and documented methodology support every result.',
  },
  {
    number: '03',
    title: 'Honest failure analysis',
    text: 'The Australia 2019 wrong-winner result is retained and explained rather than hidden or retuned away.',
  },
]

function App() {
  return (
    <main>
      <nav className="navigation">
        <a className="brand" href="#top">
          Election Polling Aggregator
        </a>

        <div className="navLinks">
          <a href="#evidence">Evidence</a>
          <a href="#methodology">Methodology</a>
          <a
            className="navButton"
            href={liveAppUrl}
            target="_blank"
            rel="noreferrer"
          >
            Open dashboard
          </a>
        </div>
      </nav>

      <section className="heroSection" id="top">
        <p className="eyebrow">
          Audited cross-country election analysis
        </p>

        <h1>
          Polling performance,
          <span> measured honestly.</span>
        </h1>

        <p className="heroText">
          A reproducible election-polling benchmark covering four
          countries, twenty-two elections and a locked chronological
          holdout.
        </p>

        <div className="heroActions">
          <a
            className="primaryButton"
            href={liveAppUrl}
            target="_blank"
            rel="noreferrer"
          >
            Explore live dashboard
          </a>

          <a
            className="secondaryButton"
            href={repositoryUrl}
            target="_blank"
            rel="noreferrer"
          >
            View source code
          </a>
        </div>
      </section>

      <section className="metricsGrid" aria-label="Project metrics">
        {metrics.map((metric) => (
          <article className="metricCard" key={metric.label}>
            <strong>{metric.value}</strong>
            <h2>{metric.label}</h2>
            <p>{metric.detail}</p>
          </article>
        ))}
      </section>

      <SectionNav />

      <AnalyticsOverview />

      <ModelEvidence />
      <PollingExplorer />
      <ScopeAudit />
      <HoldoutEvidence />
      <GovernanceEvidence />

      <section className="contentSection" id="evidence">
        <div className="sectionHeading">
          <p className="eyebrow">Evidence standard</p>
          <h2>Designed to be defensible.</h2>
        </div>

        <div className="evidenceGrid">
          {evidence.map((item) => (
            <article className="evidenceCard" key={item.number}>
              <span>{item.number}</span>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="methodologySection" id="methodology">
        <div>
          <p className="eyebrow">Selected method</p>
          <h2>Final polling average</h2>
        </div>

        <p>
          Model selection was completed using development elections.
          The final chronological holdout remains frozen and is not
          repeatedly inspected, retuned or modified.
        </p>
      </section>

      <footer>
        <p>Election Polling Aggregator</p>
        <div>
          <a
            href={repositoryUrl}
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
          <a
            href={liveAppUrl}
            target="_blank"
            rel="noreferrer"
          >
            Live dashboard
          </a>
        </div>
      </footer>
    </main>
  )
}

export default App




