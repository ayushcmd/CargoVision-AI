import React from 'react';
import { ArrowRight, CheckCircle2, Activity, Gauge, Cpu } from 'lucide-react';

interface HeroProps {
  onStartInspection: () => void;
  onExploreCapabilities: () => void;
}

export const Hero: React.FC<HeroProps> = ({ onStartInspection, onExploreCapabilities }) => {
  return (
    <section id="overview" className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden bg-[#08090B]">
      {/* Subtle background glow & grid */}
      <div className="absolute inset-0 bg-grid-pattern opacity-40 pointer-events-none"></div>
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-[#D4FF35]/5 rounded-full blur-[140px] pointer-events-none"></div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Centered Heading Content */}
        <div className="text-center max-w-3xl mx-auto">
          {/* Eyebrow */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#101113] border border-[#242529] mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-[#D4FF35]"></span>
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#9296A1]">
              Computer Vision for Rail Freight
            </span>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-[#F7F7F5] leading-[1.1]">
            Every wagon. Every detail.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#F7F7F5] via-[#D4FF35] to-[#F7F7F5]">
              One inspection platform.
            </span>
          </h1>

          {/* Supporting Text */}
          <p className="mt-6 text-base sm:text-lg text-[#9296A1] leading-relaxed max-w-2xl mx-auto">
            Turn railway footage into actionable inspection insights. Detect wagons, recognize identification numbers, inspect visible damage, and generate structured reports through one computer vision workflow.
          </p>

          {/* Action CTAs */}
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={onStartInspection}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold bg-[#D4FF35] text-[#08090B] hover:bg-[#C3EE24] transition-all shadow-lg shadow-[#D4FF35]/15"
            >
              <span>Start Inspection</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={onExploreCapabilities}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-medium bg-[#101113] text-[#F7F7F5] border border-[#242529] hover:border-[#383A42] hover:bg-[#15171B] transition-all"
            >
              Explore Capabilities
            </button>
          </div>

          {/* Compact Capability Indicators */}
          <div className="mt-8 pt-6 border-t border-[#242529]/60 flex flex-wrap items-center justify-center gap-6 text-xs text-[#9296A1]">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#D4FF35]" />
              <span>Wagon Detection</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#D4FF35]" />
              <span>Number Recognition</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#D4FF35]" />
              <span>Visual Damage Analysis</span>
            </div>
          </div>
        </div>

        {/* Hero Product Visual Preview */}
        <div className="mt-14 max-w-5xl mx-auto">
          <div className="relative rounded-2xl bg-[#101113] border border-[#242529] p-2 sm:p-3 shadow-2xl shadow-black">
            {/* Top Engineering Header Bar */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-[#242529]/80 bg-[#0D0E10] rounded-t-xl mb-2 text-xs">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#242529]"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-[#242529]"></div>
                  <div className="w-2.5 h-2.5 rounded-full bg-[#242529]"></div>
                </div>
                <span className="text-xs font-mono text-[#5E626E] ml-2">CARGOVISION-CONSOLE // RUN-1049</span>
              </div>
              <div className="flex items-center gap-4 font-mono text-[11px] text-[#9296A1]">
                <span className="hidden sm:inline flex items-center gap-1.5">
                  <Activity className="w-3 h-3 text-[#D4FF35]" /> FPS: 30.2
                </span>
                <span className="hidden sm:inline flex items-center gap-1.5">
                  <Gauge className="w-3 h-3 text-[#9296A1]" /> Speed: 62.4 km/h
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#D4FF35]/10 text-[#D4FF35] border border-[#D4FF35]/20 font-semibold">
                  ACTIVE
                </span>
              </div>
            </div>

            {/* Inspection Canvas Area */}
            <div className="relative rounded-xl overflow-hidden aspect-[16/9] sm:aspect-[21/9] bg-[#050607] border border-[#242529]/60 flex items-center justify-center">
              {/* Freight Wagon Background Asset or High-Fidelity Blueprint Canvas */}
              <img
                src="/assets/detection.png"
                alt="Wagon Detection Preview"
                className="w-full h-full object-cover opacity-85"
                onError={(e) => {
                  // Fallback to simulated blueprint if image fails to load
                  e.currentTarget.style.display = 'none';
                }}
              />

              {/* Overlaid Detection Bounding Boxes */}
              <div className="absolute inset-0 p-4 sm:p-6 flex flex-col justify-between pointer-events-none">
                {/* Simulated Bounding Box 1: Wagon Frame */}
                <div className="absolute top-[18%] left-[22%] w-[58%] h-[64%] border-2 border-[#D4FF35] rounded bg-[#D4FF35]/5 shadow-[0_0_15px_rgba(212,255,53,0.15)]">
                  <div className="absolute -top-6 left-0 px-2 py-0.5 rounded text-[10px] font-mono bg-[#D4FF35] text-[#08090B] font-bold flex items-center gap-1">
                    <span>WAGON_TRACKER #01</span>
                    <span className="opacity-80">96.8%</span>
                  </div>

                  {/* Nested Bounding Box: 11-digit OCR plate */}
                  <div className="absolute top-[34%] left-[28%] w-[42%] h-[28%] border-2 border-[#38BDF8] rounded bg-[#38BDF8]/10 shadow-[0_0_10px_rgba(56,189,248,0.2)]">
                    <div className="absolute -top-5 left-0 px-1.5 py-0.5 rounded text-[9px] font-mono bg-[#38BDF8] text-[#08090B] font-bold">
                      OCR: 31 10 148291 0 [VALID]
                    </div>
                  </div>

                  {/* Corner accents */}
                  <div className="absolute -bottom-1 -left-1 w-2 h-2 border-b-2 border-l-2 border-[#D4FF35]"></div>
                  <div className="absolute -bottom-1 -right-1 w-2 h-2 border-b-2 border-r-2 border-[#D4FF35]"></div>
                </div>

                {/* Left Telemetry HUD Badge */}
                <div className="self-start bg-[#101113]/90 backdrop-blur-md border border-[#242529] rounded-lg p-2.5 space-y-1 font-mono text-[11px] shadow-lg max-w-[220px]">
                  <div className="text-[#5E626E] text-[10px] uppercase">Telemetry Stream</div>
                  <div className="flex justify-between gap-4 text-[#F7F7F5]">
                    <span>Wagon Type:</span>
                    <span className="text-[#D4FF35] font-semibold">BOXNHL</span>
                  </div>
                  <div className="flex justify-between gap-4 text-[#F7F7F5]">
                    <span>Zone / Year:</span>
                    <span>CR / 2021</span>
                  </div>
                  <div className="flex justify-between gap-4 text-[#F7F7F5]">
                    <span>Defect Class:</span>
                    <span className="text-[#10B981]">None (Pass)</span>
                  </div>
                </div>

                {/* Right Bottom Inspection Status Badge */}
                <div className="self-end bg-[#101113]/90 backdrop-blur-md border border-[#242529] rounded-lg px-3 py-2 flex items-center gap-2.5 font-mono text-xs shadow-lg">
                  <Cpu className="w-4 h-4 text-[#D4FF35]" />
                  <div>
                    <div className="text-[10px] text-[#9296A1]">Pipeline Architecture</div>
                    <div className="text-xs font-semibold text-[#F7F7F5]">Cascaded YOLOv8 + EasyOCR</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
