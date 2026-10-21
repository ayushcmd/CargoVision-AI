import React, { useEffect, useState } from 'react';
import { FileText } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

// Types matching the Backend API responses
interface Inspection {
    id: number;
    video_name: string;
    timestamp: string;
    total_wagons: number;
}

interface Wagon {
    id: number;
    inspection_id: number;
    wagon_index: number;
    ocr_text: string;
    ocr_confidence: number;
    original_image_path: string;
    deblurred_image_path: string;
    cropped_number_path: string;
    defects: string;
    is_night: boolean;
    timestamp: string;
}

const HistoryView: React.FC = () => {
    const [inspections, setInspections] = useState<Inspection[]>([]);
    const [selectedInspection, setSelectedInspection] = useState<number | null>(null);
    const [wagons, setWagons] = useState<Wagon[]>([]);
    const [loading, setLoading] = useState(false);

    // Fetch Inspections List on Mount
    useEffect(() => {
        fetch(`${API_BASE_URL}/history`)
            .then(res => res.json())
            .then(data => setInspections(data))
            .catch(err => console.error("Failed to fetch history:", err));
    }, []);

    // Fetch Wagons when an Inspection is selected
    useEffect(() => {
        if (selectedInspection) {
            setLoading(true);
            fetch(`${API_BASE_URL}/history/${selectedInspection}`)
                .then(res => res.json())
                .then(data => {
                    setWagons(data);
                    setLoading(false);
                })
                .catch(err => {
                    console.error("Failed to fetch wagons:", err);
                    setLoading(false);
                });
        }
    }, [selectedInspection]);

    if (!selectedInspection) {
        return (
            <div className="space-y-8 animate-in fade-in duration-500">
                <div className="flex items-center gap-4 mb-8">
                    <div className="w-16 h-0.5 bg-gradient-to-r from-purple-500 to-transparent"></div>
                    <span className="text-xs tracking-[0.3em] text-purple-400 font-bold uppercase">History Module</span>
                </div>

                <div className="space-y-4">
                    {inspections.map((insp) => (
                        <div
                            key={insp.id}
                            className="bg-zinc-950 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-all"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-zinc-900 rounded-lg flex items-center justify-center">
                                        <FileText className="w-6 h-6 text-zinc-500" />
                                    </div>
                                    <div>
                                        <div className="font-semibold text-white" title={insp.video_name}>Inspection #{insp.id} - {insp.video_name}</div>
                                        <div className="text-sm text-zinc-500">{new Date(insp.timestamp).toLocaleString()}</div>
                                    </div>
                                </div>
                                <div className='flex items-center gap-4'>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation(); // Prevent card click
                                            window.open(`${API_BASE_URL}/history/${insp.id}/report`, '_blank');
                                        }}
                                        className="text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-3 py-1.5 rounded-md border border-zinc-700 transition-colors"
                                    >
                                        Report
                                    </button>
                                    <button onClick={() => setSelectedInspection(insp.id)} className="text-sm text-blue-400 hover:text-blue-300 font-medium">
                                        View Details →
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                    }
                    {
                        inspections.length === 0 && (
                            <div className="py-12 text-center text-zinc-500 border border-dashed border-zinc-800 rounded-xl">
                                No inspection history found. Run the pipeline to generate data.
                            </div>
                        )
                    }
                </div >
            </div >
        );
    }

    return (
        <div className="animate-in slide-in-from-right duration-500">
            {/* Header / Back Button */}
            <div className="flex items-center gap-4 mb-8">
                <button
                    onClick={() => setSelectedInspection(null)}
                    className="p-2 hover:bg-zinc-800 rounded-lg text-zinc-400 hover:text-white transition-colors"
                >
                    ← Back
                </button>
                <div>
                    <h2 className="text-2xl font-bold text-white">Inspection #{selectedInspection}</h2>
                    <p className="text-zinc-400 text-sm">Detailed Wagon Analysis Report</p>
                </div>
            </div>

            {loading ? (
                <div className="text-center py-20 text-zinc-500">Loading analysis data...</div>
            ) : (
                <div className="space-y-12">
                    {/* List of Wagons - Filtered to show only successful OCR */}
                    {wagons
                        .filter(wagon => wagon.ocr_text && wagon.ocr_text !== "OCR Failed")
                        .map((wagon) => (
                            <div key={wagon.id} className="border-b border-zinc-800 pb-12 last:border-0">
                                {/* Wagon Header */}
                                <div className="flex items-center gap-4 mb-6">
                                    <span className="text-xl font-bold text-white">Wagon #{wagon.wagon_index}</span>
                                    <span className="text-sm font-mono text-zinc-500">{new Date(wagon.timestamp).toLocaleString()}</span>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                                    {/* Info Panel (Reused Logic) */}
                                    <div className="md:col-span-1 bg-zinc-950/50 backdrop-blur border border-zinc-800 rounded-2xl p-6 relative overflow-hidden">
                                        <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                                            <span className="text-9xl font-mono font-bold text-white">DATA</span>
                                        </div>

                                        <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
                                            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                                            Analysis Results
                                        </h3>

                                        <div className="space-y-4 font-mono text-sm">
                                            <div className="bg-zinc-900/50 p-4 rounded-lg border border-zinc-800 space-y-3">
                                                <div className="flex justify-between items-center border-b border-white/5 pb-2">
                                                    <span className="text-zinc-400">Wagon ID:</span>
                                                    <span className="text-white font-bold bg-blue-500/20 px-2 py-0.5 rounded border border-blue-500/30">
                                                        {wagon.wagon_index}
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center">
                                                    <span className="text-zinc-400">OCR Result:</span>
                                                    <span className="text-emerald-400 font-bold">
                                                        {wagon.ocr_text || "N/A"}
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center">
                                                    <span className="text-zinc-400">Confidence:</span>
                                                    <span className="text-gray-300">
                                                        {wagon.ocr_confidence ? (wagon.ocr_confidence * 100).toFixed(1) : 0}%
                                                    </span>
                                                </div>

                                                <div className="flex justify-between items-center">
                                                    <span className="text-zinc-400">Condition:</span>
                                                    <div className="flex flex-wrap gap-2">
                                                        {wagon.is_night && (
                                                            <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded border border-purple-500/30">
                                                                Night
                                                            </span>
                                                        )}
                                                        {wagon.defects !== "None" && (
                                                            <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded border border-red-500/30">
                                                                Defect
                                                            </span>
                                                        )}
                                                        {!wagon.is_night && wagon.defects === "None" && (
                                                            <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30">
                                                                OK
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Visual Forensics Grid (Reused Logic) */}
                                    <div className="md:col-span-2 bg-zinc-950/50 backdrop-blur border border-zinc-800 rounded-2xl p-6">
                                        <h3 className="text-lg font-bold text-white mb-6">Visual Forensics</h3>

                                        <div className="grid grid-cols-2 gap-4 h-[300px]">
                                            {/* Original / Deblurred View */}
                                            <div className="space-y-2 col-span-1">
                                                <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Original Input</h4>
                                                <div className="bg-black/40 rounded-lg border border-zinc-700 h-[260px] flex items-center justify-center relative overflow-hidden group">
                                                    {wagon.original_image_path ? (
                                                        <img src={wagon.original_image_path} className="w-full h-full object-contain" alt="Original" />
                                                    ) : (
                                                        <span className="text-xs text-zinc-500 italic">No Image</span>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="space-y-2 col-span-1">
                                                <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Processed Output</h4>
                                                <div className="bg-black/40 rounded-lg border border-zinc-700 h-[260px] flex items-center justify-center relative overflow-hidden group">
                                                    {wagon.deblurred_image_path ? (
                                                        <img src={wagon.deblurred_image_path} className="w-full h-full object-contain" alt="Deblurred" />
                                                    ) : (
                                                        <span className="text-xs text-zinc-500 italic">Processing Skipped / Not Required</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* OCR Crop Row */}
                                        <div className="mt-4 pt-4 border-t border-zinc-800">
                                            <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">OCR Region</h4>
                                            <div className="bg-black/40 rounded-lg border border-zinc-700 h-[120px] flex items-center justify-center relative overflow-hidden group">
                                                {wagon.cropped_number_path ? (
                                                    <img src={wagon.cropped_number_path} className="h-full object-contain" alt="OCR Crop" />
                                                ) : (
                                                    <span className="text-xs text-zinc-500 italic">No OCR Data</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        ))}

                    {wagons.length === 0 && (
                        <div className="py-20 text-center text-zinc-500">
                            No wagons detected in this inspection.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default HistoryView;
