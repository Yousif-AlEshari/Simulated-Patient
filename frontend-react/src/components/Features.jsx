const Features = () => {
  return (
    <section id="features" className="section bg-light">
      <div className="container">
        <div className="section-header center animate-on-scroll slide-up">
          <h2>Modern Training at Your Fingertips</h2>
          <p>Give your students the best AI tools designed for mental health training.</p>
        </div>
        <div className="grid layout-4">

          <div className="feature-card animate-on-scroll slide-up" style={{ transitionDelay: '0.1s' }}>
            <div className="feature-icon bg-primary-light">
              <svg className="icon text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            </div>
            <h3>Interactive Chat</h3>
            <p>Have real conversations. Our AI talks and acts just like real patients.</p>
          </div>

          <div className="feature-card animate-on-scroll slide-up" style={{ transitionDelay: '0.2s' }}>
            <div className="feature-icon bg-secondary-light">
              <svg className="icon text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
            </div>
            <h3>Bilingual Support</h3>
            <p>Practice in both English and Arabic to better understand different cultures and communities.</p>
          </div>

          <div className="feature-card animate-on-scroll slide-up" style={{ transitionDelay: '0.3s' }}>
            <div className="feature-icon bg-success-light">
              <svg className="icon text-success" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            </div>
            <h3>Helpful Feedback</h3>
            <p>Get fast, clear grading based on standard medical rules, so you know exactly how to improve.</p>
          </div>

          <div className="feature-card animate-on-scroll slide-up" style={{ transitionDelay: '0.4s' }}>
            <div className="feature-icon bg-warning-light">
              <svg className="icon text-warning" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
            </div>
            <h3>Risk Detection</h3>
            <p>Practice handling tough situations safely. Learn how to manage patient risks without real-world danger.</p>
          </div>

        </div>
      </div>
    </section>
  );
};

export default Features;
