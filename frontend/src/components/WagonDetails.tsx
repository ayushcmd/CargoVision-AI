import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, ChevronsRight } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

interface WagonDetailsProps {
    streamId: number;
}

interface LiveWagonData {
    wagon_id: string;
    confidence: number;
    defects: string[];
    severity: 'Low' | 'Medium' | 'High' | 'None';
    // Add these optional fields to match the old UI's data
    entry_time?: string;
    speed?: string;
    source?: string;
}

const WagonDetails: React.FC<WagonDetailsProps> = ({ streamId }) => {
    const [details, setDetails] = useState<LiveWagonData | null>(null);

    useEffect(() => {
        const interval = setInterval(() => {
            // This assumes a new backend endpoint exists to provide live details per stream.
            fetch(`${API_BASE_URL}/live/wagon_details/${streamId}`)
                .then(res => {
                    if (res.ok) return res.json();
                    // On a 404 or other error (like no wagon in view), clear details.
                    return null;
                })
                .then(data => setDetails(data))
                .catch(err => {
                    console.error(`Error fetching details for stream ${streamId}:`, err);
                    setDetails(null);
                });
        }, 2000); // Poll every 2 seconds

        return () => clearInterval(interval);
    }, [streamId]);

    const hasDefects = details && details.defects.length > 0;
    const statusText = hasDefects ? 'Flagged' : 'Passed';

    // A helper for the placeholder images
    const ImagePlaceholder = ({ label, isEnhanced = false }: { label: string, isEnhanced?: boolean }) => (
        <div className="space-y-1">
            <span className={`text-[10px] uppercase ${isEnhanced ? 'text-blue-400' : 'text-zinc-500'}`}>{label}</span>
            <div className={`w-full h-20 bg-black/30 rounded border ${isEnhanced ? 'border-blue-500/30' : 'border-white/10'} flex items-center justify-center`}>
                <span className="text-xs text-zinc-600 italic">Placeholder</span>
            </div>
        </div>
    );

    return (
        <div className="space-y-4">
            {/* Header Info */}
            <div className="flex justify-between items-start border-b border-white/10 pb-3">
                <div>
                    <h4 className="text-lg font-bold text-white flex items-center gap-2">
                        {details?.wagon_id || '---'}
                        {details && (
                            <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded border border-blue-500/30">
                                {details.confidence.toFixed(1)}% Logit
                            </span>
                        )}
                    </h4>
                    <p className="text-xs text-zinc-400 mt-1">
                        In: {details?.entry_time || 'N/A'} • {details?.speed || 'N/A'} • {details?.source || 'N/A'}
                    </p>
                </div>
                <div className={`px-3 py-1 rounded text-xs font-bold ${details ? (hasDefects ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30') : 'bg-zinc-800 text-zinc-500'}`}>
                    {details ? statusText : 'IDLE'}
                </div>
            </div>

            {/* Damage Assessment */}
            <div className="space-y-2">
                <h5 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Damage Assessment</h5>
                {details && hasDefects ? (
                    <div className="flex flex-wrap items-center gap-2">
                        {details.defects.map((d, i) => (
                            <span key={i} className="text-xs bg-amber-500/10 text-amber-500 border border-amber-500/20 px-2 py-1 rounded flex items-center gap-1">
                                <AlertTriangle className="w-3 h-3" /> {d}
                            </span>
                        ))}
                        {details.severity !== 'None' && <span className="text-xs text-amber-400 font-bold ml-auto self-center">Severity: {details.severity}</span>}
                    </div>
                ) : details && !hasDefects ? (
                    <div className="flex items-center gap-2 text-emerald-400 text-sm">
                        <CheckCircle className="w-4 h-4" /> No defects detected
                    </div>
                ) : (
                    <div className="flex items-center gap-2 text-zinc-500 text-sm">
                        <ChevronsRight className="w-4 h-4" /> Awaiting data...
                    </div>
                )}
            </div>

            {/* Visual Analysis Sections */}
            <div className="space-y-3 pt-3 border-t border-white/10">
                <div className="grid grid-cols-2 gap-3">
                    <ImagePlaceholder label="Blur Mitigation (Input)" />
                    <ImagePlaceholder label="Blur Mitigation (Output)" isEnhanced />
                </div>
                <div className="grid grid-cols-2 gap-3">
                    <ImagePlaceholder label="Low Light (Input)" />
                    <ImagePlaceholder label="Low Light (Output)" isEnhanced />
                </div>
                <div className="grid grid-cols-2 gap-3">
                    <ImagePlaceholder label="OCR (Cropped)" />
                    <div className="space-y-1 flex flex-col justify-center">
                        <span className="text-[10px] text-zinc-500 uppercase">Detected ID</span>
                        <div className="text-lg font-mono font-bold text-white tracking-widest">
                            {details?.wagon_id || '---'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default WagonDetails;
