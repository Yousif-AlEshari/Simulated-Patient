const Targets = () => {
  return (
    <section id="targets" className="section bg-gradient-dark">
      <div className="container">
        <div className="section-header center text-white animate-on-scroll slide-up">
          <h2 style={{ color: 'white' }}>Made for Students and Teachers</h2>
        </div>
        <div className="grid layout-2">
          <div className="target-card animate-on-scroll slide-up">
            <div className="card-glass">
              <h3>For Psychiatry Students</h3>
              <p>Build confidence before seeing real patients. Practice complex cases anytime, improve your diagnosis skills, and get clear feedback without the stress of the real world.</p>
              <ul className="check-list">
                <li>Practice on-demand anytime</li>
                <li>Get instant feedback</li>
                <li>Practice with rare patient cases</li>
              </ul>
            </div>
          </div>
          <div className="target-card animate-on-scroll slide-up" style={{ transitionDelay: '0.2s' }}>
            <div className="card-glass">
              <h3>For Teachers and Directors</h3>
              <p>Improve your training program. Give everyone the same grading system, track student progress easily, and make sure all students reach their goals.</p>
              <ul className="check-list">
                <li>Fair and simple grading</li>
                <li>Easy-to-read student progress boards</li>
                <li>No need to schedule human actors</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Targets;
