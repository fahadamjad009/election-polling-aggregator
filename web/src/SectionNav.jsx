import { useEffect, useState } from 'react'

const sections = [
  ['analytics', 'Country performance'],
  ['model-evidence', 'Model evidence'],
  ['polling-history', 'Polling history'],
  ['scope-audit', 'Scope audit'],
  ['holdout-evidence', 'Holdout'],
  ['governance', 'Governance'],
]

function SectionNav() {
  const [active, setActive] = useState('analytics')

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.find((entry) => entry.isIntersecting)

        if (visible) {
          setActive(visible.target.id)
        }
      },
      {
        rootMargin: '-25% 0px -60% 0px',
      },
    )

    sections.forEach(([id]) => {
      const element = document.getElementById(id)

      if (element) {
        observer.observe(element)
      }
    })

    return () => observer.disconnect()
  }, [])

  return (
    <nav className="sectionNav" aria-label="Analytics sections">
      <div className="sectionNavInner">
        {sections.map(([id, label]) => (
          <a
            key={id}
            href={`#${id}`}
            className={active === id ? 'active' : ''}
          >
            {label}
          </a>
        ))}
      </div>
    </nav>
  )
}

export default SectionNav
