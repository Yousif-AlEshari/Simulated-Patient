const Navigation = () => {
  return (
    <nav className="navbar">
      <div className="container nav-container">
        <div className="logo">
          <div className="logo-text">PsychSim <span className="text-primary">Intake</span></div>
        </div>
        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#benefits">Benefits</a>
          <a href="#cta" className="btn btn-sm btn-primary">Start Practicing Now</a>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
