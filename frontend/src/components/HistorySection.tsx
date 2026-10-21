import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  Search, 
  RefreshCw, 
  CheckCircle2, 
  Clock, 
  Filter,
  Eye
} from 'lucide-react';
import { api, type Inspection } from '../config/api';

interface HistorySectionProps {
  onSelectInspection: (id: number) => void;
}

export const HistorySection: React.FC<HistorySectionProps> = ({ onSelectInspection }) => {
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const fetchHistory = async (manual = false) => {
    if (manual) setIsRefreshing(true);
    try {
      const data = await api.getHistory();
      setInspections(data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    } finally {
      setIsLoading(false);
      if (manual) setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const filteredInspections = inspections.filter(item => {
    const matchesSearch = item.video_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          item.id.toString().includes(searchQuery);
    const matchesStatus = statusFilter === 'ALL' || item.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <section id="history" className="py-24 bg-[#08090B] relative border-t border-[#242529]/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-10">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#101113] border border-[#242529] mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-[#D4FF35]"></span>
              <span className="text-[11px] font-mono uppercase tracking-widest text-[#9296A1]">
                Compliance Records
              </span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F7F7F5] tracking-tight">
              Inspection History &amp; Audits
            </h2>
            <p className="mt-2 text-sm text-[#9296A1] max-w-xl">
              Chronological log of processed freight wagon inspections, detection summaries, and downloadable PDF reports.
            </p>
          </div>

          <button
            onClick={() => fetchHistory(true)}
            disabled={isRefreshing}
            className="self-start sm:self-auto inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-mono bg-[#101113] text-[#F7F7F5] border border-[#242529] hover:border-[#383A42] hover:bg-[#15171B] transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-[#D4FF35]' : 'text-[#9296A1]'}`} />
            <span>Reload Records</span>
          </button>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-6 p-2 rounded-2xl bg-[#101113] border border-[#242529]">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-[#5E626E] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by video name or run ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-xl text-xs bg-[#0D0E10] border border-[#242529] text-[#F7F7F5] placeholder-[#5E626E] focus:outline-none focus:border-[#D4FF35]/50 font-mono"
            />
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <span className="text-xs font-mono text-[#5E626E] hidden sm:inline flex items-center gap-1">
              <Filter className="w-3 h-3" /> Status:
            </span>
            {['ALL', 'COMPLETED', 'PROCESSING'].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                  statusFilter === status
                    ? 'bg-[#D4FF35]/15 text-[#D4FF35] border border-[#D4FF35]/30 font-semibold'
                    : 'text-[#9296A1] hover:text-[#F7F7F5] border border-transparent'
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>

        {/* History Table / Cards */}
        {isLoading ? (
          <div className="py-16 text-center text-xs font-mono text-[#5E626E]">
            Loading audit records from SQLite engine...
          </div>
        ) : filteredInspections.length === 0 ? (
          <div className="rounded-2xl bg-[#101113] border border-[#242529] p-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-[#1A1C20] border border-[#242529] flex items-center justify-center mx-auto mb-4 text-[#5E626E]">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-[#F7F7F5]">No Inspection Records Found</h3>
            <p className="mt-1 text-xs text-[#9296A1] max-w-sm mx-auto">
              Run your first video inspection from the workspace above to generate audit documentation.
            </p>
          </div>
        ) : (
          <div className="rounded-2xl bg-[#101113] border border-[#242529] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs font-mono">
                <thead>
                  <tr className="border-b border-[#242529] bg-[#0D0E10] text-[#5E626E] text-[11px] uppercase">
                    <th className="py-3 px-4">Run ID</th>
                    <th className="py-3 px-4">Footage File</th>
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4">Wagons</th>
                    <th className="py-3 px-4">Performance</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#242529]/60">
                  {filteredInspections.map((insp) => (
                    <tr 
                      key={insp.id}
                      className="hover:bg-[#15171B] transition-colors group"
                    >
                      <td className="py-3.5 px-4 font-bold text-[#F7F7F5]">
                        #{insp.id}
                      </td>
                      <td className="py-3.5 px-4 font-medium text-[#F7F7F5] max-w-xs truncate" title={insp.video_name}>
                        {insp.video_name}
                      </td>
                      <td className="py-3.5 px-4 text-[#9296A1]">
                        {insp.timestamp}
                      </td>
                      <td className="py-3.5 px-4 text-[#F7F7F5] font-bold">
                        {insp.total_wagons}
                      </td>
                      <td className="py-3.5 px-4 text-[#9296A1]">
                        {insp.fps ? `${insp.fps.toFixed(1)} FPS` : 'N/A'} • {insp.resolution || '360x640'}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-bold ${
                          insp.status === 'COMPLETED'
                            ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30'
                            : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                        }`}>
                          {insp.status === 'COMPLETED' ? (
                            <CheckCircle2 className="w-2.5 h-2.5" />
                          ) : (
                            <Clock className="w-2.5 h-2.5 animate-spin" />
                          )}
                          <span>{insp.status}</span>
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => onSelectInspection(insp.id)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-mono text-[#9296A1] hover:text-[#F7F7F5] hover:bg-[#16171B] border border-[#242529] transition-colors"
                          >
                            <Eye className="w-3 h-3 text-[#D4FF35]" />
                            <span>View</span>
                          </button>
                          <a
                            href={api.getReportDownloadUrl(insp.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-mono text-[#F7F7F5] bg-[#16171B] hover:bg-[#1E2025] border border-[#242529] hover:border-[#D4FF35]/40 transition-colors"
                          >
                            <Download className="w-3 h-3 text-[#38BDF8]" />
                            <span>PDF</span>
                          </a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
