import { useState } from 'react'
import './LandingPage.css'

const STEPS = [
  { name: 'Plans', detail: 'Breaks your question into smaller sub-tasks before searching for anything.' },
  { name: 'Research', detail: 'Searches the web and your knowledge base in parallel, pulling from multiple sources.' },
  { name: 'Synthesize', detail: 'Merges findings from every source into a single draft answer.' },
  { name: 'Critique', detail: 'Checks its own draft against the sources before showing you anything.' },
]

const PLANS = [
  {
    name: 'Free', price: '$0', cadence: '/month',
    blurb: 'Try Rune on a handful of questions.',
    features: ['5 research queries / month', 'Web search only', 'Standard depth'],
    cta: 'Start free',
  },
  {
    name: 'Pro', price: '$20', cadence: '/month',
    blurb: 'For regular, deeper research.',
    features: ['Unlimited research queries', 'Web + knowledge base search', 'Deep research mode', 'Session history'],
    cta: 'Get Pro', highlight: true,
  },
  {
    name: 'Max', price: '$60', cadence: '/month',
    blurb: 'For teams running Rune constantly.',
    features: ['Everything in Pro', 'Priority queueing', 'Shared team sessions', 'Priority support'],
    cta: 'Get Max',
  },
]

export default function LandingPage({ onGetStarted, onLogin }) {
  const [query, setQuery] = useState('')

  function handleAskRune() {
    onGetStarted(query)
  }

  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="landing-logo">
          <img src="/Rune.png" alt="Rune logo" width="24" height="24" style={{ objectFit: 'contain', borderRadius: 4 }} />
          <span className="landing-logo-text">Rune</span>
        </div>
        <div className="landing-nav-links">
          <a href="#how-it-works">How it works</a>
          <a href="#pricing">Pricing</a>
        </div>
        <div className="landing-nav-actions">
          <button className="landing-link-btn" onClick={() => onLogin()}>Log in</button>
          <button className="landing-cta-btn" onClick={() => onGetStarted()}>Try Rune</button>
        </div>
      </nav>

      <header className="landing-hero">
        <h1 className="landing-headline">
          Meet your<br />research partner
        </h1>
        <p className="landing-subhead">Untangle any messy, murky, multi-source question with Rune</p>

        <div className="landing-input-bar">
          <input
            type="text"
            placeholder="Ask Rune Anything..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAskRune()}
          />
          <button className="landing-ask-btn" onClick={handleAskRune}>
            Ask Rune <span aria-hidden="true">↑</span>
          </button>
        </div>

        <div className="landing-quick-actions">
          <button className="landing-quick-btn" onClick={() => onGetStarted('Help me research a topic')}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Research
          </button>
          <button className="landing-quick-btn" onClick={() => onGetStarted('Fact-check a claim for me')}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
            Fact-check
          </button>
          <button className="landing-quick-btn" onClick={() => onGetStarted('Compare two things for me')}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
            Compare
          </button>
        </div>
      </header>

      <section id="how-it-works" className="landing-section">
        <h2 className="landing-section-title">How it works</h2>
        <div className="landing-steps">
          {STEPS.map((step) => (
            <div className="landing-step" key={step.name}>
              <h3>{step.name}</h3>
              <p>{step.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="pricing" className="landing-section">
        <h2 className="landing-section-title">Pricing</h2>
        <div className="landing-pricing-grid">
          {PLANS.map((plan) => (
            <div className={`landing-price-card${plan.highlight ? ' highlight' : ''}`} key={plan.name}>
              <h3>{plan.name}</h3>
              <div className="landing-price-row">
                <span className="landing-price">{plan.price}</span>
                <span className="landing-cadence">{plan.cadence}</span>
              </div>
              <p className="landing-plan-blurb">{plan.blurb}</p>
              <ul className="landing-feature-list">
                {plan.features.map((f) => <li key={f}>{f}</li>)}
              </ul>
              <button className="landing-plan-cta" onClick={() => onGetStarted()}>{plan.cta}</button>
            </div>
          ))}
        </div>
      </section>

      <footer className="landing-footer">
        <span>© 2026 Rune</span>
      </footer>
    </div>
  )
}