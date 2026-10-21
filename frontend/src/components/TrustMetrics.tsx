import React from 'react';
import { ShieldCheck, Database, Clock, Eye } from 'lucide-react';

export const TrustMetrics: React.FC = () => {
  const specs = [
    {
      icon: Clock,
      value: '~33 ms',
      label: 'Nominal Frame Latency',
      description: 'Single-frame inference pipeline target operating at 30 FPS under hardware acceleration.'
    },
    {
      icon: ShieldCheck,
      value: '11-Digit Standard',
      label: 'Indian Railways Format',
      description: 'Strict algorithmic checksum verification separating wagon type, zone code, and manufacturing year.'
    },
    {
      icon: Eye,
      value: '12+ Defect Classes',
      label: 'Mechanical Anomaly Taxonomy',
      description: 'Includes door latch displacement, damaged axle components, displaced coil springs, and exterior cracks.'
    },
    {
      icon: Database,
      value: 'Zero-Loss SQLite Audit',
      label: 'Compliance Persistence',
      description: 'Local inspection metadata, crop paths, and validation scores permanently archived without external telemetry leakage.'
    }
  ];

  return (
    <section className="py-20 bg-[#08090B] relative border-t border-[#242529]/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="max-w-2xl mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#101113] border border-[#242529] mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-[#D4FF35]"></span>
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#9296A1]">
              Engineering Benchmarks
            </span>
          </div>

          <h2 className="text-3xl font-extrabold text-[#F7F7F5] tracking-tight">
            Built for rigorous yard &amp; trackside inspection.
          </h2>

          <p className="mt-3 text-sm text-[#9296A1] leading-relaxed">
            Engineered around verifiable railway standards, modular neural cascades, and local edge data integrity.
          </p>
        </div>

        {/* 4 Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {specs.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="rounded-2xl bg-[#101113] border border-[#242529] p-6 flex flex-col justify-between"
              >
                <div>
                  <div className="w-9 h-9 rounded-xl bg-[#1A1C20] border border-[#242529] flex items-center justify-center text-[#D4FF35] mb-5">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="text-2xl font-extrabold font-mono text-[#F7F7F5]">
                    {item.value}
                  </div>
                  <div className="text-xs font-mono text-[#D4FF35] mt-1 font-semibold">
                    {item.label}
                  </div>
                </div>

                <p className="mt-4 text-xs text-[#9296A1] leading-relaxed border-t border-[#242529]/60 pt-4">
                  {item.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
