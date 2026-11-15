import { CtaFooter } from "@/features/landing/CtaFooter";
import { HeroSection } from "@/features/landing/HeroSection";
import { HowSection } from "@/features/landing/HowSection";
import { LandingHeader } from "@/features/landing/LandingHeader";
import { RouteSection } from "@/features/landing/RouteSection";
import { WhySection } from "@/features/landing/WhySection";

export default function Landing() {
  return (
    <div className="overflow-x-clip">
      <LandingHeader />
      <main>
        <HeroSection />
        <HowSection />
        <RouteSection />
        <WhySection />
        <CtaFooter />
      </main>
    </div>
  );
}
