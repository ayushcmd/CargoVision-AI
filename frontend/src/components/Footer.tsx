import React from 'react';
import { Github } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

export const Footer: React.FC = () => {
  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <footer className="bg-[#050608] border-t border-[#242529] py-14 text-xs font-mono text-[#5E626E]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 mb-12">
          {/* Brand Info */}
          <div className="md:col-span-5 space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-md bg-[#101113] border border-[#242529] flex items-center justify-center">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 6H20M4 18H20M9 6V18M15 6V18" stroke="#D4FF35" strokeWidth="2" strokeLinecap="round"/>
                  <circle cx="12" cy="12" r="3" fill="#D4FF35" fillOpacity="0.2" stroke="#D4FF35" strokeWidth="1.5"/>
                </svg>
              </div>
              <span className="font-bold text-sm tracking-tight text-[#F7F7F5]">
                CargoVision <span className="text-[#D4FF35]">AI</span>
              </span>
            </div>

            <p className="text-xs text-[#9296A1] leading-relaxed max-w-sm">
              Industrial computer vision platform for freight wagon detection, 11-digit Indian Railways identification OCR, low-light image recovery, and damage auditing.
            </p>

            <div className="pt-2 flex items-center gap-2 text-[11px] text-[#5E626E]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]"></span>
              <span>Core Server Connected: {API_BASE_URL.replace(/^https?:\/\//, '')}</span>
            </div>
          </div>

          {/* Quick Nav */}
          <div className="md:col-span-3 space-y-2">
            <div className="text-[11px] uppercase tracking-wider text-[#F7F7F5] font-semibold mb-3">
              Navigation
            </div>
            <ul className="space-y-2 text-[#9296A1]">
              <li>
                <button onClick={() => scrollTo('overview')} className="hover:text-[#D4FF35] transition-colors">
                  Overview
                </button>
              </li>
              <li>
                <button onClick={() => scrollTo('capabilities')} className="hover:text-[#D4FF35] transition-colors">
                  Capabilities
                </button>
              </li>
              <li>
                <button onClick={() => scrollTo('workspace')} className="hover:text-[#D4FF35] transition-colors">
                  Interactive Workspace
                </button>
              </li>
              <li>
                <button onClick={() => scrollTo('analytics')} className="hover:text-[#D4FF35] transition-colors">
                  Analytics &amp; Telemetry
                </button>
              </li>
              <li>
                <button onClick={() => scrollTo('history')} className="hover:text-[#D4FF35] transition-colors">
                  Inspection History
                </button>
              </li>
            </ul>
          </div>

          {/* Attribution & Legal */}
          <div className="md:col-span-4 space-y-2">
            <div className="text-[11px] uppercase tracking-wider text-[#F7F7F5] font-semibold mb-3">
              Open Source Attribution
            </div>
            <p className="text-xs text-[#9296A1] leading-relaxed">
              Based on the open-source <strong className="text-[#F7F7F5]">GARUD</strong> project originally developed by <strong className="text-[#F7F7F5]">P47Parzival</strong> under the MIT License.
            </p>
            <div className="pt-2">
              <a
                href="https://github.com/P47Parzival/low-light-image-deblur.git"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-[#38BDF8] hover:text-[#7DD3FC] transition-colors"
              >
                <Github className="w-3.5 h-3.5" />
                <span>Upstream Source Repository</span>
              </a>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t border-[#242529]/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-[#5E626E]">
          <div>
            &copy; {new Date().getFullYear()} CargoVision AI. All rights reserved. Retaining upstream MIT license.
          </div>
          <div className="flex items-center gap-4">
            <span>YOLOv8 (Ultralytics)</span>
            <span>&bull;</span>
            <span>EasyOCR (JaidedAI)</span>
            <span>&bull;</span>
            <span>Zero-DCE</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
