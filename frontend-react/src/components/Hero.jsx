const Hero = () => {
  return (
    <header className="hero">
      <div className="hero-bg-glow"></div>
      <div className="container hero-container">
        <div className="hero-content animate-on-scroll slide-up">
          <div className="badge">Built for Excellent Care</div>
          <h1 className="hero-title">Practice Patient Interviews with <span className="gradient-text">AI</span> Simulation</h1>
          <p className="hero-subtitle">Improve your training with realistic patient conversations. Safe and easy-to-use practice for future mental health professionals.</p>
          <div className="hero-actions">
            <a href="#cta" className="btn btn-primary btn-lg">Start Practicing Now</a>
            <a href="#how-it-works" className="btn btn-secondary btn-lg">See How It Works ➜</a>
          </div>
        </div>
        <div className="hero-visual animate-on-scroll slide-in-right">
          <div className="glass-panel main-dashboard">
            <div className="dashboard-header">
              <div className="dots">
                <span></span><span></span><span></span>
              </div>
              <div className="dashboard-title">Patient Session</div>
            </div>
            <div className="chat-interface">
              <div className="chat-bubble bot">
                <p>Hello. I've been feeling really exhausted lately, and I just can't seem to focus on my classes anymore.</p>
              </div>
              <div className="chat-bubble user">
                <p>I'm sorry to hear that. How long have you been experiencing this exhaustion and lack of focus?</p>
              </div>
              <div className="chat-bubble bot">
                <p>It's been about two months now. Even when I sleep 10 hours, I wake up tired.</p>
              </div>
              <div className="analysis-panel">
                <div className="analysis-item">
                  <span className="indicator success"></span>
                  <div>
                    <strong>Empathy Detected</strong>
                    <p className="text-sm">Excellent opening validation of the patient's concern.</p>
                  </div>
                </div>
                <div className="analysis-item">
                  <span className="indicator info"></span>
                  <div>
                    <strong>Diagnostic Goal</strong>
                    <p className="text-sm">Assess standard SIGECAPS criteria.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Hero;
