import React, { useState, useEffect } from 'react';
import { Upload } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

interface Wagon {
    id: number;
    wagon_index: number;
    ocr_text: string;
    original_image_path: string;
    deblurred_image_path: string;
    cropped_number_path: string;
    anomaly_image_path: string;
    anomaly_type: string;
}

const UploadView: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [status, setStatus] = useState<string | null>(null);
    const [inspectionId, setInspectionId] = useState<number | null>(null);
    const [wagons, setWagons] = useState<Wagon[]>([]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            setFile(selectedFile);
            setPreviewUrl(URL.createObjectURL(selectedFile));
            setStatus(null);
            setInspectionId(null);
            setProcessing(false);
            setWagons([]);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setStatus("Uploading Video...");
        setWagons([]);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                setStatus("Upload complete. Processing initiated...");
                setInspectionId(data.inspection_id);
                setProcessing(true);
            } else {
                setStatus("Upload failed. Check server logs.");
                setUploading(false); // Only reset if failed
            }
        } catch (error) {
            console.error(error);
            setStatus("Network error during upload.");
            setUploading(false);
        }
    };

    // Polling Effect
    useEffect(() => {
        let interval: any;

        if (processing && inspectionId) {
            interval = setInterval(async () => {
                try {
                    // 1. Check Status
                    const res = await fetch(`${API_BASE_URL}/inspections/${inspectionId}/status`);
                    if (res.ok) {
                        const data = await res.json();
                        if (data.status === 'COMPLETED') {
                            setStatus("Processing Complete! Check History Tab to view results. ✅");
                            setProcessing(false);
                            setUploading(false);
                            clearInterval(interval);
                        } else {
                            setStatus((prev) => prev === "Processing..." ? "Processing.. " : "Processing...");
                        }
                    }

                    // 2. Fetch Live Wagons
                    const wagonRes = await fetch(`${API_BASE_URL}/history/${inspectionId}`);
                    if (wagonRes.ok) {
                        const wagonData = await wagonRes.json();
                        setWagons(wagonData);
                    }

                } catch (e) {
                    console.error("Polling error", e);
                }
            }, 2000); // Check every 2 seconds
        }

        return () => clearfix(interval);
    }, [processing, inspectionId]);

    // Helper to fix TS error with clearInterval
    const clearfix = (i: any) => clearInterval(i);

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="flex items-center gap-4 mb-8">
                <div className="w-16 h-0.5 bg-gradient-to-r from-blue-500 to-transparent"></div>
                <span className="text-xs tracking-[0.3em] text-blue-400 font-bold uppercase">Upload Module</span>
            </div>

            {/* If no file is selected, show the big upload button */}
            {!file && (
                <div className="border-2 border-dashed border-zinc-800 rounded-2xl p-16 text-center hover:border-zinc-700 transition-all bg-zinc-950/50 relative">
                    <input
                        type="file"
                        accept="video/*"
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        id="video-upload"
                        onChange={handleFileChange}
                        disabled={uploading}
                    />
                    <label htmlFor="video-upload" className="cursor-pointer">
                        <Upload className="w-16 h-16 text-zinc-600 mx-auto mb-6" />
                        <h3 className="text-xl font-bold text-white mb-2">Upload Video Files</h3>
                        <p className="text-zinc-500 mb-6">Drag and drop your inspection videos here</p>
                        <span className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg">
                            Select Files
                        </span>
                    </label>
                </div>
            )}

            {/* If a file is selected, show preview and controls */}
            {previewUrl && (
                <div className="bg-zinc-950/70 border border-zinc-800 rounded-2xl p-6 relative overflow-hidden flex flex-col gap-4">
                    <h3 className="text-sm font-bold text-zinc-400 uppercase">Preview &amp; Process</h3>

                    {/* Video Wrapper with Overlay or Stream */}
                    <div className="flex-1 bg-black rounded-lg overflow-hidden border border-zinc-700 relative aspect-video">
                        {processing && inspectionId ? (
                            <div className="absolute inset-0 z-20 bg-black flex flex-col items-center justify-center">
                                {/* Use MJPEG Stream for Live Preview */}
                                <img
                                    src={`${API_BASE_URL}/stream/processing/${inspectionId}`}
                                    alt="Live Processing Feed"
                                    className="w-full h-full object-contain"
                                    onError={(e) => {
                                        // Fallback if stream fails
                                        e.currentTarget.style.display = 'none';
                                    }}
                                />
                                <div className="absolute bottom-4 right-4 bg-black/70 px-3 py-1 text-xs text-green-400 font-mono rounded border border-green-900 animate-pulse">
                                    LIVE PROCESSING
                                </div>
                            </div>
                        ) : (
                            <video src={previewUrl} controls className="w-full h-full object-contain" />
                        )}
                    </div>

                    <div className="flex justify-between items-center bg-zinc-900/50 p-3 rounded-lg border border-zinc-800">
                        <div className='flex flex-col'>
                            <span className={`text-sm font-bold ${status && status.includes("Complete") ? "text-emerald-400" : "text-amber-400"}`}>
                                {status || file?.name}
                            </span>
                            {status && <span className='text-xs text-zinc-500'>{file?.name}</span>}
                        </div>
                        {!processing && (
                            <button
                                onClick={handleUpload}
                                disabled={uploading}
                                className={`bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-6 py-2 rounded-lg font-semibold transition-all ml-auto ${uploading ? 'hidden' : ''}`}
                            >
                                Start Processing
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* LIVE DETECTION GRID */}
            {wagons.length > 0 && (
                <div className="bg-zinc-950/70 border border-zinc-800 rounded-2xl p-6 relative overflow-hidden flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="flex justify-between items-center">
                        <h3 className="text-sm font-bold text-zinc-400 uppercase">Live Detections ({wagons.length})</h3>
                        <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                            <span className="text-xs text-red-400 font-mono">LIVE FEED</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 max-h-[600px] overflow-y-auto pr-2">
                        {[...wagons].reverse().map((wagon) => (
                            <div key={wagon.id} className="bg-black/40 border border-zinc-800 rounded-lg p-3 hover:border-zinc-600 transition-all group">
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <div className="text-xs text-zinc-500 font-mono">#{wagon.wagon_index}</div>
                                        <div className="text-sm font-bold text-white font-mono">{wagon.ocr_text || "Scanning..."}</div>
                                    </div>
                                    {wagon.anomaly_type && (
                                        <div className="bg-red-900/40 border border-red-800/50 text-red-200 text-[10px] px-2 py-0.5 rounded uppercase font-bold tracking-wider animate-pulse">
                                            {wagon.anomaly_type}
                                        </div>
                                    )}
                                </div>

                                <div className="grid grid-cols-2 gap-2 mt-2">
                                    {/* Images */}
                                    <div className="space-y-1">
                                        <span className="text-[10px] text-zinc-600 uppercase block">Original</span>
                                        <div className="aspect-video bg-zinc-900 rounded overflow-hidden border border-zinc-800/50">
                                            {wagon.original_image_path ? (
                                                <img src={wagon.original_image_path} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                                            ) : <div className="w-full h-full flex items-center justify-center text-zinc-800 text-[10px]">N/A</div>}
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <span className="text-[10px] text-zinc-600 uppercase block">Deblurred</span>
                                        <div className="aspect-video bg-zinc-900 rounded overflow-hidden border border-zinc-800/50">
                                            {wagon.deblurred_image_path ? (
                                                <img src={wagon.deblurred_image_path} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                                            ) : <div className="w-full h-full flex items-center justify-center text-zinc-800 text-[10px]">N/A</div>}
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <span className="text-[10px] text-zinc-600 uppercase block">OCR Crop</span>
                                        <div className="aspect-video bg-zinc-900 rounded overflow-hidden border border-zinc-800/50">
                                            {wagon.cropped_number_path ? (
                                                <img src={wagon.cropped_number_path} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                                            ) : <div className="w-full h-full flex items-center justify-center text-zinc-800 text-[10px]">N/A</div>}
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <span className={`text-[10px] uppercase block ${wagon.anomaly_type ? 'text-red-400 font-bold' : 'text-zinc-600'}`}>Anomaly</span>
                                        <div className={`aspect-video bg-zinc-900 rounded overflow-hidden border ${wagon.anomaly_type ? 'border-red-500/50 shadow-[0_0_10px_rgba(220,38,38,0.2)]' : 'border-zinc-800/50'}`}>
                                            {wagon.anomaly_image_path ? (
                                                <img src={wagon.anomaly_image_path} className="w-full h-full object-cover" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center text-zinc-800 text-[10px]">
                                                    {wagon.anomaly_type ? 'IMG ERR' : 'PASS'}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default UploadView;
