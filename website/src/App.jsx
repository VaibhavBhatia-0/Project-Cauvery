import { useEffect, useState } from 'react'
import Hero from './components/Hero.jsx'
import { Numbers, HowItWorks, DidYouKnow, Footer } from './components/Story.jsx'
import Allocate from './components/Allocate.jsx'
import Results from './components/Results.jsx'

const LINKS = [
  ['numbers', 'Project'],
  ['how', 'How it works'],
  ['allocation', 'Allocation'],
  ['results', 'Results'],
]

function Nav() {
  const [active, setActive] = useState('')
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: '-45% 0px -50% 0px' },
    )
    LINKS.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el) })
    return () => io.disconnect()
  }, [])
  return (
    <nav className="nav" aria-label="Sections">
      <div className="container nav-in">
        <a href="#top" className="nav-brand"><span className="logo" aria-hidden="true">≈</span>Cauvery</a>
        <div className="nav-links">
          {LINKS.map(([id, label]) => (
            <a key={id} href={`#${id}`} className={active === id ? 'on' : ''}>{label}</a>
          ))}
        </div>
        <a className="btn-lime nav-cta" href="#allocation">Simulator <span aria-hidden="true">→</span></a>
      </div>
    </nav>
  )
}

export default function App() {
  // Fade sections in once they reach the viewport (anything above it is shown too,
  // so jumping via the nav never leaves hidden content behind).
  useEffect(() => {
    let raf = 0
    const check = () => {
      raf = 0
      const limit = window.innerHeight * 0.92
      document.querySelectorAll('.reveal:not(.in)').forEach((el) => {
        if (el.getBoundingClientRect().top < limit) el.classList.add('in')
      })
    }
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(check) }
    check()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => { window.removeEventListener('scroll', onScroll); window.removeEventListener('resize', onScroll) }
  }, [])

  return (
    <div id="top">
      <Nav />
      <Hero />
      <main>
        <Numbers />
        <HowItWorks />
        <DidYouKnow />
        <Allocate />
        <Results />
      </main>
      <Footer />
    </div>
  )
}
