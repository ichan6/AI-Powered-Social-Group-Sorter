import './AboutPage.css'
import dev_pfp from '../assets/datkoreancoder.jpeg'

function AboutPage() {
  return (
    <div id="about-page">
      {/* Left 1/3: Profile image */}
      <div id="about-profile">
        <img
          id="profile-picture"
          src={dev_pfp} // Replace with actual path once uploaded
          alt="Developer Profile"
        />
      </div>

      {/* Right 2/3: Description sections */}
      <div id="about-content">
        <section className="about-section">
          <h2 className="about-heading">Who am I?</h2>
          <p className="about-paragraph">
            Hello! I’m Ian — a private developer and the creator of this Family Sorting App.
            I’m passionate about making tools that actually help people solve real problems, 
            especially when it comes to organizing large groups efficiently and meaningfully.
          </p>
        </section>

        <section className="about-section">
          <h2 className="about-heading">Why This App?</h2>
          <p className="about-paragraph">
            This app was designed to solve a recurring challenge faced by student orgs and community groups:
            sorting members into balanced and meaningful "families" each term. What started as a manual,
            time-consuming process is now simplified through AI-assisted logic and automation — giving 
            organizers more time to focus on what matters: building connections.
          </p>
        </section>

        <footer id="contact-info">
          <h3>Need support or found a bug?</h3>
          <p>Contact me at: <strong>ichan6@illinois.edu</strong></p>
        </footer>
      </div>
    </div>
  )
}

export default AboutPage
