const Roadmap = () => {
  return (
    <section id="roadmap" className="section bg-light">
      <div className="container">
        <div className="roadmap-header animate-on-scroll slide-up">
          <span className="badge badge-secondary">Roadmap</span>
          <h2>The Future of Training</h2>
          <p>We are always improving medical education. Here is what's coming soon.</p>
        </div>
        <div className="grid layout-2 mt-lg">
          <div className="roadmap-card animate-on-scroll slide-up">
            <div className="icon-wrapper">🥽</div>
            <h4>Virtual Reality</h4>
            <p>Step into a virtual clinic. Practice reading body language and making eye contact in a 3D world.</p>
          </div>
          <div className="roadmap-card animate-on-scroll slide-up" style={{ transitionDelay: '0.1s' }}>
            <div className="icon-wrapper">🎭</div>
            <h4>Better Realism</h4>
            <p>Realistic avatars that show real emotions, pauses in speech, and expressions that match their diagnosis.</p>
          </div>
          {/*<div className="roadmap-card animate-on-scroll slide-up" style={{ transitionDelay: '0.2s' }}>
            <div className="icon-wrapper">📅</div>
            <h4>Patient Follow-Ups</h4>
            <p>Follow patients across multiple visits over time to practice long-term care and managing medication.</p>
          </div>*/}
        </div>
      </div>
    </section>
  );
};

export default Roadmap;
