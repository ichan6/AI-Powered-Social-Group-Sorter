import './LandingPage.css'
import mikuBanner from '../assets/hatsune_miku.jpg'

function LandingPage() {
  return (
    <div className="landing-wrapper">
      {/* HERO SECTION */}
      <section className="section hero-section full-page">
        <div className="hero-banner">
          <img src={mikuBanner} alt="App Logo" className="banner-img" />
        </div>
        <h1 className="section-title">Family Sorting App</h1>
        <p className="hero-subtitle">
          The GPT-powered social sorting tool your retreat never knew it needed.
        </p>
      </section>

      {/* LOGO MARQUEE */}
      <div className="logo-marquee-wrapper">
        <div className="logo-marquee">
          <span>🏢 ZorboTech</span>
          <span>🎉 VibeSquad</span>
          <span>🚀 Nebula Housing</span>
          <span>☕ Cool Beans Inc.</span>
          <span>👥 Friend.ly</span>
          <span>🏠 HouseHub</span>
          <span>🔮 VibeForge</span>
          <span>Yuh yuh Inc</span>
          <span>Eshketit and Co</span>
          <span>🎭 DramaTech</span>
        </div>
      </div>

      {/* SUMMARY SECTION */}
      <section className="section full-page">
        <h2 className="section-title">What This App Does</h2>
        <p className="section-text">
          Upload your CSV of members, add optional grouping instructions,
          and this app will intelligently form social groups based on GPT analysis
          of form responses, shared values, emotional tone, and stated preferences.
        </p>
        <p className="section-text">
          It’s like Hogwarts House Sorting, but smarter — and cooler 😎
        </p>

        <div className="testimonials">
          <p>🗣️ “I met my soulmate because of this.” — Some guy</p>
          <p>🧠 “Truly changed the way I see vibes.” — Definitely not the dev</p>
          <p>🎩 “It’s like Hogwarts House Sorting but more chaotic.” — Probably someone cool</p>
        </div>
      </section>

      {/* TERMS SECTION */}
      <section className="section full-page">
        <h2 className="section-title">Terms of Use</h2>
        <ul className="tos-list">
          <li>Do not share access keys without permission.</li>
          <li>Usage is tracked (e.g., time, IP, file size) for moderation + billing.</li>
          <li>Unauthorized abuse may result in revoked access.</li>
          <li>OpenAI API usage may incur real costs — please be respectful.</li>
        </ul>
        <p>If you have questions or issues, please contact the developer.</p>
      </section>
    </div>
  )
}

export default LandingPage
