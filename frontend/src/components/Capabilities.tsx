import React from 'react';
import { 
  Scan, 
  Binary, 
  AlertTriangle, 
  Moon, 
  BarChart3, 
  FileSpreadsheet,
  ArrowUpRight
} from 'lucide-react';

interface CapabilitiesProps {
  onSelectCapability?: (key: string) => void;
}

export const Capabilities: React.FC<CapabilitiesProps> = () => {
  const capabilities = [
    {
      icon: Scan,
      title: 'Wagon Detection',
      tag: 'YOLOv8',
      description: 'Continuous localization, spatial bounding, and multi-wagon tracking across variable-speed freight footage.',
      details: 'Custom-trained model tracks wagons across frame sequences to isolate individual rolling stock units.'
    },
    {
      icon: Binary,
      title: 'Wagon Number Recognition',
      tag: 'OCR Engine',
      description: 'Automated identification and OCR text extraction of standard 11-digit Indian Railways wagon identifiers.',
      details: 'Parses wagon type code, owning railway zone, manufacturing year, and performs algorithmic checksum verification.'
    },
    {
      icon: AlertTriangle,
      title: 'Damage Analysis',
      tag: 'Anomaly Classifier',
      description: 'Detection and localization of physical defects, open wagon doors, spring displacements, and structural faults.',
      details: 'Provides localized anomaly alerts with confidence scores to highlight critical maintenance concerns.'
    },
    {
      icon: Moon,
      title: 'Low-Light Enhancement',
      tag: 'Zero-DCE',
      description: 'Illumination recovery and dynamic curve estimation for nighttime transit, yard sidings, and low-lux tunnels.',
      details: 'Enhances under-exposed frames prior to downstream detection without introducing synthetic artifacts.'
    },
    {
      icon: BarChart3,
      title: 'Inspection Analytics',
      tag: 'Live Telemetry',
      description: 'Real-time aggregation of wagon throughput, transit speeds, illumination metrics, and anomaly ratios.',
      details: 'Extracts frame processing speeds, blur metrics, and defect distribution across historical inspection runs.'
    },
    {
      icon: FileSpreadsheet,
      title: 'Inspection Reports',
      tag: 'Audit PDF',
      description: 'One-click generation of structured compliance inspection documentation with visual proof clips and timestamps.',
      details: 'Standardized executive PDF exports ready for railway engineers, maintenance yards, and regulatory compliance.'
    }
  ];

  return (
    <section id="capabilities" className="py-24 bg-[#08090B] relative border-t border-[#242529]/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#101113] border border-[#242529] mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-[#D4FF35]"></span>
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#9296A1]">
              Capabilities
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F7F7F5] tracking-tight">
            A clearer view of every freight inspection.
          </h2>

          <p className="mt-4 text-base text-[#9296A1] leading-relaxed">
            From wagon identification to visual damage analysis, bring the key stages of railway inspection into one workflow.
          </p>
        </div>

        {/* 6-Card Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {capabilities.map((cap, idx) => {
            const Icon = cap.icon;
            return (
              <div
                key={idx}
                className="group relative rounded-2xl bg-[#101113] border border-[#242529] p-6 hover:border-[#383A42] hover:bg-[#15171B] transition-all duration-200 flex flex-col justify-between"
              >
                <div>
                  {/* Top: Icon + Tech Tag */}
                  <div className="flex items-center justify-between mb-5">
                    <div className="w-10 h-10 rounded-xl bg-[#1A1C20] border border-[#242529] flex items-center justify-center text-[#D4FF35] group-hover:border-[#D4FF35]/30 group-hover:bg-[#D4FF35]/10 transition-colors">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[11px] font-mono text-[#5E626E] group-hover:text-[#9296A1] transition-colors border border-[#242529] rounded px-2 py-0.5 bg-[#0D0E10]">
                      {cap.tag}
                    </span>
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-bold text-[#F7F7F5] group-hover:text-white transition-colors flex items-center gap-1.5">
                    <span>{cap.title}</span>
                    <ArrowUpRight className="w-4 h-4 text-[#5E626E] opacity-0 group-hover:opacity-100 group-hover:text-[#D4FF35] transition-all" />
                  </h3>

                  {/* Description */}
                  <p className="mt-2 text-sm text-[#9296A1] leading-relaxed">
                    {cap.description}
                  </p>
                </div>

                {/* Footer details */}
                <div className="mt-6 pt-4 border-t border-[#242529]/60 text-xs text-[#5E626E] font-mono">
                  {cap.details}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
