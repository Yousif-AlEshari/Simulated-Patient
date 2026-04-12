// Components
import Navigation from '../components/Navigation';
import Hero from '../components/Hero';
import Features from '../components/Features';
import HowItWorks from '../components/HowItWorks';
import Targets from '../components/Targets';
import Benefits from '../components/Benefits';
import Roadmap from '../components/Roadmap';
import CallToAction from '../components/CallToAction';
import Footer from '../components/Footer';

// Hooks
import useGlobalAnimations from '../hooks/useGlobalAnimations';

const LandingPage = () => {
  // Initialize scroll observers for the landing page elements
  useGlobalAnimations();

  return (
    <>
      <Navigation />
      <Hero />
      <Features />
      <HowItWorks />
      <Targets />
      <Benefits />
      <Roadmap />
      <CallToAction />
      <Footer />
    </>
  );
};

export default LandingPage;
