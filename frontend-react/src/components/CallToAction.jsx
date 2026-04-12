import { Link } from 'react-router-dom';

const CallToAction = () => {
  return (
    <section id="cta" className="cta-section">
      <div className="container cta-container animate-on-scroll slide-up">
        <h2>Ready to Improve Your Training Program?</h2>
        <p>Join top medical schools in providing safer, smarter, and easier mental health education.</p>
        <div className="cta-actions">
          <Link to="/cases" className="btn btn-primary btn-lg">Start Practicing</Link>
          <a href="#features" className="btn btn-outline btn-lg text-white">Learn More</a>
        </div>
      </div>
    </section >
  );
};

export default CallToAction;
