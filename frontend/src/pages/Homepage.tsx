import React, { useState } from 'react';
import { Navbar } from '../components/Navbar';
import { Hero } from '../components/Hero';
import { Capabilities } from '../components/Capabilities';
import { Workspace } from '../components/Workspace';
import { AnalyticsSection } from '../components/AnalyticsSection';
import { TrustMetrics } from '../components/TrustMetrics';
import { HowItWorks } from '../components/HowItWorks';
import { HistorySection } from '../components/HistorySection';
import { Footer } from '../components/Footer';

export const Homepage: React.FC = () => {
  const [activeInspectionId, setActiveInspectionId] = useState<number | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = useState<number>(0);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleSelectInspection = (id: number) => {
    setActiveInspectionId(id);
    scrollTo('workspace');
  };

  const handleInspectionComplete = () => {
    // Increment key to trigger history & analytics refresh
    setHistoryRefreshKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-[#08090B] text-[#F7F7F5] selection:bg-[#D4FF35] selection:text-[#08090B]">
      {/* Top Navbar */}
      <Navbar 
        onStartInspection={() => scrollTo('workspace')}
        onOpenHistory={() => scrollTo('history')}
      />

      <main>
        {/* 1. Hero Section */}
        <Hero 
          onStartInspection={() => scrollTo('workspace')}
          onExploreCapabilities={() => scrollTo('capabilities')}
        />

        {/* 2. Capabilities Grid */}
        <Capabilities />

        {/* 3. Interactive Inspection Workspace */}
        <Workspace 
          key={activeInspectionId || 'default-workspace'}
          initialInspectionId={activeInspectionId}
          onInspectionComplete={handleInspectionComplete}
        />

        {/* 4. Analytics & Telemetry */}
        <AnalyticsSection key={`analytics-${historyRefreshKey}`} />

        {/* 5. Engineering Trust & Metrics */}
        <TrustMetrics />

        {/* 6. Process Flow */}
        <HowItWorks />

        {/* 7. History & Audit Records */}
        <HistorySection 
          key={`history-${historyRefreshKey}`}
          onSelectInspection={handleSelectInspection}
        />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default Homepage;
