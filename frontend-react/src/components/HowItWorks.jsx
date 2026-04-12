const HowItWorks = () => {
  return (
    <section id="how-it-works" className="section">
      <div className="container">
        <div className="section-header center animate-on-scroll slide-up">
          <h2>How to Start in Three Steps</h2>
          <p>A simple process designed for easy learning.</p>
        </div>

        <div className="timeline">
          <div className="timeline-item animate-on-scroll slide-in-left">
            <div className="timeline-badge">1</div>
            <div className="timeline-content">
              <h3>Pick a Patient Case</h3>
              <p>Select a patient case from a diverse range of available clinical scenarios, ranging from depression to severe mental health issues.</p>
            </div>
          </div>
          <div className="timeline-item animate-on-scroll slide-in-right">
            <div className="timeline-badge">2</div>
            <div className="timeline-content">
              <h3>Talk to the Patient</h3>
              <p>Chat naturally using text or voice. Ask questions, check the patient's condition, and figure out the diagnosis in a safe space.</p>
            </div>
          </div>
          <div className="timeline-item animate-on-scroll slide-in-left">
            <div className="timeline-badge">3</div>
            <div className="timeline-content">
              <h3>Review Your Results</h3>
              <p>Instantly see how well you did, including what you did right, your accuracy, and where you need to improve.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
