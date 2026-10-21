import React, { useState } from 'react';
import { Camera, FileText, Download, Activity, TrendingUp, BarChart3, Settings } from 'lucide-react';

import VideoFeed from '../components/VideoFeed';
import WagonDetails from '../components/WagonDetails';
import StatsPanel from '../components/StatsPanel';
import Navbar from '../components/Navbar';
import UploadView from '../components/UploadView';
import HistoryView from '../components/HistoryView';
import Analysis from './Analysis';

function App() {
  const [activeTab, setActiveTab] = useState('Live');
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    setMousePosition({ x: e.clientX, y: e.clientY });
  };

  return (
    <div className="min-h-screen text-white overflow-x-hidden" onMouseMove={handleMouseMove}>
      {/* Enhanced gradient background */}
      <div className="fixed inset-0 opacity-20 pointer-events-none">
        <div
          className="absolute w-[1200px] h-[1200px] rounded-full blur-[200px] transition-all duration-700 ease-out"
          style={{
            background: 'radial-gradient(circle, rgba(59, 130, 246, 0.12) 0%, rgba(168, 85, 247, 0.08) 50%, transparent 70%)',
            left: `${mousePosition.x - 600}px`,
            top: `${mousePosition.y - 600}px`,
          }}
        ></div>
      </div>

      {/* Scanline effect */}
      <div className="fixed inset-0 opacity-[0.03] pointer-events-none" style={{
        backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(255, 255, 255, 0.02) 1px, rgba(255, 255, 255, 0.02) 2px)',
      }}></div>

      {/* Grid overlay */}
      <div className="fixed inset-0 opacity-[0.06]">
        <div className="absolute inset-0" style={{
          backgroundImage: `
            linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}></div>
      </div>

      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content */}
      <main className="relative pt-24 pb-20 px-10 max-w-[1920px] mx-auto">
        {activeTab === 'Live' ? (
          <div className="space-y-8">
            {/* Main Camera Feed - Large at Top */}
            <div className="group relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-3xl blur-xl opacity-0 group-hover:opacity-75 transition-opacity duration-500"></div>

              <div className="relative bg-black/30 backdrop-blur-2xl border border-white/10 rounded-2xl overflow-hidden shadow-2xl group-hover:border-blue-500/20 transition-all duration-300">
                {/* Compact Header */}
                <div className="relative px-4 py-2 border-b border-white/10 bg-black/20">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-600/20 border border-blue-500/30 flex items-center justify-center">
                        <Camera className="w-4 h-4 text-blue-400" />
                      </div>
                      <div>
                        <h2 className="font-semibold text-white text-sm">Primary Camera</h2>
                        <div className="text-xs text-zinc-500 font-mono">CAM_01</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
                      <span className="text-xs text-emerald-400 font-semibold">LIVE</span>
                    </div>
                  </div>
                </div>

                {/* Large Video Feed */}
                <div className="h-[400px]">
                  <VideoFeed streamId={1} />
                </div>
              </div>
            </div>

            {/* Secondary Camera Feeds - Two Small Below */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {[2, 3].map((streamId) => (
                <div key={streamId} className="group relative">
                  <div className="absolute -inset-1 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-3xl blur-xl opacity-0 group-hover:opacity-75 transition-opacity duration-500"></div>

                  <div className="relative bg-black/30 backdrop-blur-2xl border border-white/10 rounded-2xl overflow-hidden shadow-2xl group-hover:border-blue-500/20 transition-all duration-300">
                    {/* Header */}
                    <div className="relative px-4 py-2 border-b border-white/10 bg-black/20">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-600/20 border border-blue-500/30 flex items-center justify-center">
                            <Camera className="w-4 h-4 text-blue-400" />
                          </div>
                          <div>
                            <h2 className="font-semibold text-white text-sm">Camera Stream {streamId}</h2>
                            <div className="text-xs text-zinc-500 font-mono">CAM_UNIT_0{streamId}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50"></div>
                          <span className="text-xs text-emerald-400 font-semibold">ACTIVE</span>
                        </div>
                      </div>
                    </div>

                    {/* Video Feed */}
                    <div className="h-[350px]">
                      <VideoFeed streamId={streamId} />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Wagon Details Section - Complete Information Extracted from Video */}
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-500/15 to-purple-500/15 rounded-3xl blur-2xl opacity-50"></div>

              <div className="relative bg-black/30 backdrop-blur-2xl border border-white/10 rounded-3xl overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="p-8 border-b border-white/10 bg-black/20">
                  <div className="flex items-center justify-between">
                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="h-1 w-16 bg-gradient-to-r from-blue-500 via-purple-500 to-transparent rounded-full"></div>
                        <span className="text-xs tracking-[0.4em] text-blue-400 font-bold uppercase">Extracted Data</span>
                      </div>
                      <h2 className="text-4xl font-black tracking-tight text-white">Wagon Information</h2>
                      <p className="text-zinc-400">Complete details extracted from video streams using AI analysis</p>
                    </div>

                    <div className="flex items-center gap-3">
                      <button className="px-5 py-3 bg-zinc-900/50 hover:bg-zinc-800/70 border border-zinc-700 rounded-xl text-sm font-semibold text-zinc-300 hover:text-white transition-all duration-200 flex items-center gap-2">
                        <Settings className="w-4 h-4" />
                        Configure
                      </button>
                      <button className="px-5 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 rounded-xl text-sm font-semibold text-white transition-all duration-200 shadow-lg shadow-blue-500/30 flex items-center gap-2">
                        <Download className="w-4 h-4" />
                        Export Data
                      </button>
                    </div>
                  </div>
                </div>

                {/* Wagon Details Content */}
                <div className="p-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map((streamId) => (
                    <div key={streamId} className="space-y-4 bg-black/20 rounded-xl p-6 border border-white/5">
                      <div className="flex items-center gap-3 pb-4 border-b border-white/10">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-600/20 border border-blue-500/30 flex items-center justify-center">
                          <span className="text-sm font-bold text-blue-400">{streamId}</span>
                        </div>
                        <h3 className="font-bold text-white text-lg">Stream {streamId} Details</h3>
                      </div>
                      <WagonDetails streamId={streamId} />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Enhanced Stats Section */}
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500/15 to-blue-500/15 rounded-3xl blur-2xl opacity-50"></div>

              <div className="relative bg-black/30 backdrop-blur-2xl border border-white/10 rounded-3xl overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="p-8 border-b border-white/10 bg-black/20">
                  <div className="flex items-center justify-between">
                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="h-1 w-16 bg-gradient-to-r from-emerald-500 via-sky-500 to-transparent rounded-full"></div>
                        <span className="text-xs tracking-[0.4em] text-emerald-400 font-bold uppercase">System Analytics</span>
                      </div>
                      <h2 className="text-4xl font-black tracking-tight text-white">Performance Dashboard</h2>
                      <p className="text-zinc-400">Comprehensive overview of inspection metrics and system health</p>
                    </div>

                    <button className="px-5 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 rounded-xl text-sm font-semibold text-white transition-all duration-200 shadow-lg shadow-blue-500/30 flex items-center gap-2">
                      <Download className="w-4 h-4" />
                      Export Report
                    </button>
                  </div>
                </div>

                {/* Stats Panel */}
                <div className="p-8 space-y-8">
                  {/* Status Dashboard */}
                  <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    {/* System Status Card */}
                    <div className="lg:col-span-2 bg-black/20 backdrop-blur-lg border border-white/10 rounded-2xl p-6 shadow-2xl">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                            <Activity className="w-6 h-6 text-white" />
                          </div>
                          <div>
                            <div className="text-sm text-zinc-400 mb-1">System Status</div>
                            <div className="text-2xl font-bold text-white mb-2">Fully Operational</div>
                            <div className="text-sm text-zinc-300">All camera feeds active • AI processing at 99.4% accuracy</div>
                          </div>
                        </div>
                        <div className="w-3 h-3 bg-emerald-400 rounded-full shadow-lg shadow-emerald-400/50"></div>
                      </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="bg-black/20 backdrop-blur-lg border border-white/10 rounded-2xl p-6 shadow-xl">
                      <div className="flex items-center gap-3 mb-3">
                        <TrendingUp className="w-5 h-5 text-emerald-400" />
                        <div className="text-xs text-zinc-400 uppercase tracking-wider">Processing</div>
                      </div>
                      <div className="text-3xl font-black text-white mb-1">24/7</div>
                      <div className="text-sm text-zinc-400">Continuous Operation</div>
                    </div>

                    <div className="bg-black/20 backdrop-blur-lg border border-white/10 rounded-2xl p-6 shadow-xl">
                      <div className="flex items-center gap-3 mb-3">
                        <BarChart3 className="w-5 h-5 text-sky-400" />
                        <div className="text-xs text-zinc-400 uppercase tracking-wider">Streams</div>
                      </div>
                      <div className="text-3xl font-black text-white mb-1">3/3</div>
                      <div className="text-sm text-zinc-400">Active Cameras</div>
                    </div>
                  </div>
                  <StatsPanel />
                </div>
              </div>
            </div>
          </div>
        ) : (
          activeTab === 'Upload' ? (
            <UploadView />
          ) : activeTab === 'History' ? (
            <HistoryView />
          ) : activeTab === 'Reports' ? (
            <Analysis />
          ) : (
            <div className="space-y-8">
              <div className="flex items-center gap-4">
                <div className="h-1 w-16 bg-gradient-to-r from-purple-500 to-transparent rounded-full"></div>
                <span className="text-xs tracking-[0.3em] text-purple-400 font-bold uppercase">Coming Soon</span>
              </div>
              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-purple-500/15 to-pink-500/15 rounded-3xl blur-2xl opacity-50"></div>
                <div className="relative bg-black/30 backdrop-blur-2xl border border-white/10 rounded-3xl p-32 text-center shadow-2xl">
                  <div className="w-24 h-24 mx-auto mb-8 bg-gradient-to-br from-purple-600 via-purple-500 to-pink-600 rounded-3xl flex items-center justify-center shadow-2xl shadow-purple-500/30 rotate-3 group-hover:rotate-6 transition-transform duration-300">
                    <FileText className="w-12 h-12 text-white" />
                  </div>
                  <h2 className="text-4xl font-black text-white mb-4">{activeTab} Module</h2>
                  <p className="text-lg text-zinc-400 max-w-lg mx-auto">This feature is currently under active development. Check back soon for updates and new capabilities!</p>
                </div>
              </div>
            </div>
          )
        )}
      </main>
    </div>
  );
}

export default App;