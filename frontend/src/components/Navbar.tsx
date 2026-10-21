import React, { useState } from 'react';
import { Menu, X, ArrowRight, ShieldCheck, ChevronDown } from 'lucide-react';

interface NavbarProps {
  onStartInspection?: () => void;
  onOpenHistory?: () => void;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onStartInspection, onOpenHistory, onTabChange }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [selectorOpen, setSelectorOpen] = useState(false);

  const scrollTo = (id: string) => {
    if (onTabChange) {
      onTabChange(id);
    }
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#08090B]/85 backdrop-blur-md border-b border-[#242529]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Brand + Product Selector */}
          <div className="flex items-center gap-4">
            <a href="#overview" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-[#101113] border border-[#242529] flex items-center justify-center group-hover:border-[#D4FF35]/50 transition-colors">
                {/* Custom geometric railway cargo vision icon */}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 6H20M4 18H20M9 6V18M15 6V18" stroke="#D4FF35" strokeWidth="2" strokeLinecap="round"/>
                  <circle cx="12" cy="12" r="3" fill="#D4FF35" fillOpacity="0.2" stroke="#D4FF35" strokeWidth="1.5"/>
                </svg>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-base tracking-tight text-[#F7F7F5]">
                  CargoVision <span className="text-[#D4FF35]">AI</span>
                </span>
              </div>
            </a>

            {/* Outlined Product Selector */}
            <div className="hidden sm:block relative">
              <button
                onClick={() => setSelectorOpen(!selectorOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-medium text-[#9296A1] bg-[#101113] border border-[#242529] hover:border-[#383A42] hover:text-[#F7F7F5] transition-all"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-[#D4FF35] animate-pulse"></span>
                <span>Inspection Platform</span>
                <ChevronDown className="w-3 h-3 text-[#9296A1]" />
              </button>

              {selectorOpen && (
                <div className="absolute left-0 mt-2 w-56 rounded-lg bg-[#101113] border border-[#242529] p-2 shadow-xl shadow-black/80 z-50 animate-in fade-in zoom-in-95 duration-150">
                  <div className="px-2.5 py-1.5 text-[11px] font-mono uppercase text-[#5E626E] border-b border-[#242529]/60">
                    Active Environment
                  </div>
                  <div className="px-2.5 py-2 mt-1 rounded bg-[#16171B] border border-[#242529]">
                    <div className="flex items-center gap-2 text-xs font-medium text-[#F7F7F5]">
                      <ShieldCheck className="w-3.5 h-3.5 text-[#D4FF35]" />
                      <span>Trackside Engine v1.0.0</span>
                    </div>
                    <p className="text-[11px] text-[#9296A1] mt-0.5 font-mono">Status: Ready (Local Core)</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Center Navigation Links */}
          <nav className="hidden md:flex items-center gap-7">
            <button
              onClick={() => scrollTo('overview')}
              className="text-xs font-medium text-[#9296A1] hover:text-[#F7F7F5] transition-colors"
            >
              Overview
            </button>
            <button
              onClick={() => scrollTo('capabilities')}
              className="text-xs font-medium text-[#9296A1] hover:text-[#F7F7F5] transition-colors"
            >
              Capabilities
            </button>
            <button
              onClick={() => scrollTo('workspace')}
              className="text-xs font-medium text-[#9296A1] hover:text-[#F7F7F5] transition-colors flex items-center gap-1.5"
            >
              <span>Workspace</span>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-[#D4FF35]/10 text-[#D4FF35] border border-[#D4FF35]/20">Live</span>
            </button>
            <button
              onClick={() => scrollTo('analytics')}
              className="text-xs font-medium text-[#9296A1] hover:text-[#F7F7F5] transition-colors"
            >
              Analytics
            </button>
            <button
              onClick={() => scrollTo('how-it-works')}
              className="text-xs font-medium text-[#9296A1] hover:text-[#F7F7F5] transition-colors"
            >
              How It Works
            </button>
          </nav>

          {/* Right Action Buttons */}
          <div className="hidden sm:flex items-center gap-3">
            <button
              onClick={() => {
                if (onOpenHistory) onOpenHistory();
                scrollTo('history');
              }}
              className="text-xs font-medium text-[#9296A1] hover:text-[#F7F7F5] px-3 py-1.5 rounded-lg border border-transparent hover:border-[#242529] hover:bg-[#101113] transition-all"
            >
              Inspection History
            </button>
            <button
              onClick={() => {
                if (onStartInspection) onStartInspection();
                scrollTo('workspace');
              }}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-[#F7F7F5] text-[#08090B] hover:bg-[#D4FF35] transition-colors shadow-sm"
            >
              <span>Start Inspection</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 rounded-lg text-[#9296A1] hover:text-[#F7F7F5] hover:bg-[#101113] border border-transparent hover:border-[#242529]"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#242529] bg-[#08090B] px-4 pt-2 pb-4 space-y-2 animate-in slide-in-from-top-2 duration-150">
          <button
            onClick={() => scrollTo('overview')}
            className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-[#9296A1] hover:text-[#F7F7F5] hover:bg-[#101113]"
          >
            Overview
          </button>
          <button
            onClick={() => scrollTo('capabilities')}
            className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-[#9296A1] hover:text-[#F7F7F5] hover:bg-[#101113]"
          >
            Capabilities
          </button>
          <button
            onClick={() => scrollTo('workspace')}
            className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-[#9296A1] hover:text-[#F7F7F5] hover:bg-[#101113]"
          >
            Workspace
          </button>
          <button
            onClick={() => scrollTo('analytics')}
            className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-[#9296A1] hover:text-[#F7F7F5] hover:bg-[#101113]"
          >
            Analytics
          </button>
          <button
            onClick={() => scrollTo('how-it-works')}
            className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-[#9296A1] hover:text-[#F7F7F5] hover:bg-[#101113]"
          >
            How It Works
          </button>
          <button
            onClick={() => scrollTo('history')}
            className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-[#9296A1] hover:text-[#F7F7F5] hover:bg-[#101113]"
          >
            Inspection History
          </button>
          <div className="pt-2">
            <button
              onClick={() => {
                if (onStartInspection) onStartInspection();
                scrollTo('workspace');
              }}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold bg-[#D4FF35] text-[#08090B]"
            >
              <span>Start Inspection</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;
