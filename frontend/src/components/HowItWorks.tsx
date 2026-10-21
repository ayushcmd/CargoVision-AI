import React from 'react';
import { UploadCloud, Cpu, CheckSquare, FileDown } from 'lucide-react';

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      num: '01',
      icon: UploadCloud,
      title: 'Ingest Trackside Footage',
      description: 'Upload high-speed line footage or connect trackside RTSP camera feeds via standard video formats.'
    },
    {
      num: '02',
      icon: Cpu,
      title: 'Cascaded Vision Pipeline',
      description: 'The neural cascade detects wagons, localizes serial plates, applies Zero-DCE enhancement, and classifies damage.'
    },
    {
      num: '03',
      icon: CheckSquare,
      title: 'Audit & Format Verification',
      description: 'Extracted serials pass through an algorithmic 11-digit checksum engine to confirm wagon zone, type, and ID validity.'
    },
    {
      num: '04',
      icon: FileDown,
      title: 'Download Structured Report',
      description: 'Generate an audit-ready executive PDF report complete with visual image crops, defect flags, and telemetry metrics.'
    }
  ];

  return (
    <section id="how-it-works" className="py-24 bg-[#08090B] relative border-t border-[#242529]/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#101113] border border-[#242529] mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-[#D4FF35]"></span>
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#9296A1]">
              Process Flow
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F7F7F5] tracking-tight">
            How CargoVision AI Operates
          </h2>

          <p className="mt-4 text-base text-[#9296A1] leading-relaxed">
            From raw rolling stock video to structured compliance documentation in four automated steps.
          </p>
        </div>

        {/* 4-Step Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={idx}
                className="relative rounded-2xl bg-[#101113] border border-[#242529] p-6 flex flex-col justify-between hover:border-[#383A42] transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <span className="text-2xl font-mono font-black text-[#242529] group-hover:text-[#383A42]">
                      {step.num}
                    </span>
                    <div className="w-9 h-9 rounded-xl bg-[#1A1C20] border border-[#242529] flex items-center justify-center text-[#D4FF35]">
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>

                  <h3 className="text-base font-bold text-[#F7F7F5] mb-2">
                    {step.title}
                  </h3>

                  <p className="text-xs text-[#9296A1] leading-relaxed">
                    {step.description}
                  </p>
                </div>

                <div className="mt-6 pt-3 border-t border-[#242529]/60 flex items-center gap-2 text-[11px] font-mono text-[#5E626E]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#D4FF35]/70"></span>
                  <span>Automated Step</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
