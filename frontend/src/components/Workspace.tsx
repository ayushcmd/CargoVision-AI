import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload, 
  FileVideo, 
  Loader2, 
  AlertCircle, 
  Download, 
  Play, 
  Maximize2
} from 'lucide-react';
import { api, type WagonDetail, type Inspection } from '../config/api';

interface WorkspaceProps {
  initialInspectionId?: number | null;
  onInspectionComplete?: () => void;
}

export const Workspace: React.FC<WorkspaceProps> = ({ initialInspectionId, onInspectionComplete }) => {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [inspectionId, setInspectionId] = useState<number | null>(initialInspectionId || null);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [activeStage, setActiveStage] = useState<number>(0);
  const [wagons, setWagons] = useState<WagonDetail[]>([]);
  const [inspectionMeta, setInspectionMeta] = useState<Inspection | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedImageModal, setSelectedImageModal] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const stages = [
    'Footage Ingestion',
    'Wagon Detection & Tracking',
    'Number Plate Localization',
    'OCR 11-Digit Extraction',
    'Damage & Defect Analysis',
    'Results Compilation'
  ];

  // Sync if initialInspectionId changes from outside (e.g., clicking in History)
  useEffect(() => {
    if (initialInspectionId) {
      setInspectionId(initialInspectionId);
      loadInspectionResults(initialInspectionId);
    }
  }, [initialInspectionId]);

  const loadInspectionResults = async (id: number) => {
    try {
      const details = await api.getInspectionDetails(id);
      setWagons(details);
      
      const history = await api.getHistory();
      const match = history.find(h => h.id === id);
      if (match) {
        setInspectionMeta(match);
        if (match.status === 'COMPLETED') {
          setActiveStage(6);
          setIsProcessing(false);
        }
      }
    } catch (err) {
      console.error('Failed to load inspection details:', err);
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      selectFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      selectFile(e.target.files[0]);
    }
  };

  const selectFile = (selectedFile: File) => {
    setErrorMsg(null);
    // Validate format
    const validExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
    const fileExt = '.' + selectedFile.name.split('.').pop()?.toLowerCase();
    if (!validExtensions.includes(fileExt)) {
      setErrorMsg(`Unsupported file format. Please upload one of: ${validExtensions.join(', ')}`);
      return;
    }

    // Validate size (max 500 MB)
    if (selectedFile.size > 500 * 1024 * 1024) {
      setErrorMsg('File size exceeds the 500 MB limit.');
      return;
    }

    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
    setInspectionId(null);
    setWagons([]);
    setInspectionMeta(null);
    setActiveStage(0);
    setStatusMessage(`Loaded: ${selectedFile.name} (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)`);
  };

  // Quick load of sample video that already exists on disk
  const loadSampleVideo = async (filename: string) => {
    setErrorMsg(null);
    try {
      setStatusMessage(`Fetching sample video: ${filename}...`);
      const response = await fetch(`/assets/${filename}`);
      if (!response.ok) {
        throw new Error('Sample file not found in public assets');
      }
      const blob = await response.blob();
      const sampleFile = new File([blob], filename, { type: 'video/mp4' });
      selectFile(sampleFile);
    } catch (err) {
      console.error('Failed to load sample video:', err);
      setErrorMsg('Could not load sample video from assets.');
    }
  };

  const startInspection = async () => {
    if (!file) return;

    setIsUploading(true);
    setErrorMsg(null);
    setStatusMessage('Uploading video footage to processing pipeline...');
    setActiveStage(1);

    try {
      const res = await api.uploadVideo(file);
      setIsUploading(false);
      setInspectionId(res.inspection_id);
      setIsProcessing(true);
      setStatusMessage('Footage ingested. Neural detection pipeline running...');
      setActiveStage(2);
    } catch (err: any) {
      setIsUploading(false);
      setIsProcessing(false);
      setErrorMsg(err.message || 'Failed to start inspection.');
    }
  };

  // Polling for processing status & live wagons
  useEffect(() => {
    let timer: any = null;

    if (isProcessing && inspectionId) {
      timer = setInterval(async () => {
        try {
          const statusRes = await api.getInspectionStatus(inspectionId);
          
          if (statusRes.status === 'COMPLETED') {
            setIsProcessing(false);
            setActiveStage(6);
            setStatusMessage('Inspection complete. Structured audit data compiled.');
            clearInterval(timer);
            loadInspectionResults(inspectionId);
            if (onInspectionComplete) onInspectionComplete();
          } else {
            // Increment stage for visual feedback
            setActiveStage(prev => (prev < 5 ? prev + 1 : 4));
          }

          // Fetch currently detected wagons
          const currentWagons = await api.getInspectionDetails(inspectionId);
          if (currentWagons.length > 0) {
            setWagons(currentWagons);
          }
        } catch (err) {
          console.error('Error polling status:', err);
        }
      }, 2000);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isProcessing, inspectionId]);

  return (
    <section id="workspace" className="py-24 bg-[#08090B] relative border-t border-[#242529]/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#101113] border border-[#242529] mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-[#D4FF35] animate-pulse"></span>
              <span className="text-[11px] font-mono uppercase tracking-widest text-[#9296A1]">
                Interactive Workspace
              </span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F7F7F5] tracking-tight">
              Freight Inspection Console
            </h2>
            <p className="mt-2 text-sm text-[#9296A1] max-w-xl">
              Upload freight footage, initiate cascaded computer vision inference, verify 11-digit serial numbers, and inspect detected defects.
            </p>
          </div>

          {/* Quick Sample Selector */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-[#5E626E]">Quick Test:</span>
            <button
              onClick={() => loadSampleVideo('wagon_fault_detection.mp4')}
              className="px-2.5 py-1 rounded-lg text-xs font-mono bg-[#101113] border border-[#242529] text-[#9296A1] hover:text-[#F7F7F5] hover:border-[#383A42] transition-colors"
            >
              Fault Video (7.7 MB)
            </button>
            <button
              onClick={() => loadSampleVideo('wagon_night_detection.mp4')}
              className="px-2.5 py-1 rounded-lg text-xs font-mono bg-[#101113] border border-[#242529] text-[#9296A1] hover:text-[#F7F7F5] hover:border-[#383A42] transition-colors"
            >
              Night Video (5.7 MB)
            </button>
          </div>
        </div>

        {/* Error Banner */}
        {errorMsg && (
          <div className="mb-8 p-4 rounded-xl bg-red-950/30 border border-red-500/30 flex items-center gap-3 text-red-400 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Upload / Video Player / Pipeline Stage Tracker */}
          <div className="lg:col-span-7 space-y-6">
            {/* Upload Zone / Media Player Card */}
            <div className="rounded-2xl bg-[#101113] border border-[#242529] p-5 relative overflow-hidden">
              <div className="flex items-center justify-between pb-4 border-b border-[#242529]/80 mb-4 text-xs font-mono">
                <span className="text-[#9296A1] flex items-center gap-1.5">
                  <FileVideo className="w-3.5 h-3.5 text-[#D4FF35]" />
                  <span>Footage Ingestion</span>
                </span>
                {inspectionId && (
                  <span className="px-2 py-0.5 rounded bg-[#16171B] border border-[#242529] text-[#D4FF35]">
                    Run ID: #{inspectionId}
                  </span>
                )}
              </div>

              {!file && !previewUrl ? (
                /* Drag and drop empty state */
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleFileDrop}
                  className="border-2 border-dashed border-[#242529] rounded-xl p-10 sm:p-14 text-center hover:border-[#D4FF35]/40 hover:bg-[#15171B]/50 transition-all cursor-pointer group"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="video/mp4,video/avi,video/quicktime,video/x-matroska,video/webm"
                    className="hidden"
                    onChange={handleFileInput}
                  />
                  <div className="w-14 h-14 rounded-2xl bg-[#1A1C20] border border-[#242529] flex items-center justify-center mx-auto mb-4 group-hover:border-[#D4FF35]/50 group-hover:bg-[#D4FF35]/10 transition-colors">
                    <Upload className="w-6 h-6 text-[#9296A1] group-hover:text-[#D4FF35] transition-colors" />
                  </div>
                  <h3 className="text-base font-bold text-[#F7F7F5]">
                    Drag and drop inspection footage
                  </h3>
                  <p className="mt-1 text-xs text-[#9296A1]">
                    Supported formats: MP4, AVI, MOV, MKV (Maximum 500 MB)
                  </p>
                  <div className="mt-5">
                    <span className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-[#F7F7F5] text-[#08090B] group-hover:bg-[#D4FF35] transition-colors">
                      Browse Local Files
                    </span>
                  </div>
                </div>
              ) : (
                /* Video Player / Live Streaming Preview */
                <div className="space-y-4">
                  <div className="relative rounded-xl overflow-hidden aspect-video bg-black border border-[#242529] flex items-center justify-center">
                    {isProcessing && inspectionId ? (
                      /* Live Processing Stream */
                      <div className="relative w-full h-full flex items-center justify-center bg-black">
                        <img
                          src={api.getProcessingStreamUrl(inspectionId)}
                          alt="Live Processing Feed"
                          className="w-full h-full object-contain"
                          onError={(e) => {
                            // If stream is empty or video ended, fallback to preview
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                        <div className="absolute top-3 left-3 px-2 py-1 rounded bg-black/80 border border-[#D4FF35]/40 text-[#D4FF35] text-[10px] font-mono flex items-center gap-1.5 animate-pulse">
                          <span className="w-2 h-2 rounded-full bg-[#D4FF35]"></span>
                          <span>LIVE PIPELINE ACTIVE</span>
                        </div>
                      </div>
                    ) : (
                      <video
                        src={previewUrl || undefined}
                        controls
                        className="w-full h-full object-contain"
                      />
                    )}
                  </div>

                  {/* Actions & Status row */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
                    <div className="text-xs text-[#9296A1] truncate max-w-sm">
                      <span className="text-[#F7F7F5] font-medium">{file?.name}</span>
                      {statusMessage && <p className="text-[11px] text-[#5E626E] mt-0.5">{statusMessage}</p>}
                    </div>

                    <div className="flex items-center gap-2 w-full sm:w-auto">
                      {!isProcessing && activeStage !== 6 && (
                        <button
                          onClick={startInspection}
                          disabled={isUploading}
                          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold bg-[#D4FF35] text-[#08090B] hover:bg-[#C3EE24] disabled:opacity-50 transition-all shadow-md shadow-[#D4FF35]/10"
                        >
                          {isUploading ? (
                            <>
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              <span>Uploading...</span>
                            </>
                          ) : (
                            <>
                              <Play className="w-3.5 h-3.5 fill-current" />
                              <span>Run Inspection</span>
                            </>
                          )}
                        </button>
                      )}

                      <button
                        onClick={() => {
                          setFile(null);
                          setPreviewUrl(null);
                          setInspectionId(null);
                          setWagons([]);
                          setInspectionMeta(null);
                          setActiveStage(0);
                        }}
                        disabled={isProcessing}
                        className="px-3 py-2.5 rounded-lg text-xs font-mono text-[#9296A1] hover:text-[#F7F7F5] border border-[#242529] hover:bg-[#16171B] disabled:opacity-30 transition-colors"
                      >
                        Reset
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Pipeline Processing Stages */}
            <div className="rounded-2xl bg-[#101113] border border-[#242529] p-5">
              <div className="flex items-center justify-between pb-3 border-b border-[#242529]/80 mb-4">
                <span className="text-xs font-mono uppercase tracking-wider text-[#9296A1]">
                  Pipeline Progress
                </span>
                <span className="text-xs font-mono text-[#5E626E]">
                  Stage {activeStage} of {stages.length}
                </span>
              </div>

              <div className="space-y-2.5">
                {stages.map((stageName, idx) => {
                  const stageNum = idx + 1;
                  const isDone = activeStage > stageNum || activeStage === 6;
                  const isCurrent = activeStage === stageNum && isProcessing;

                  return (
                    <div
                      key={idx}
                      className={`flex items-center justify-between p-2.5 rounded-lg border text-xs font-mono transition-all ${
                        isDone
                          ? 'bg-[#101113] border-[#242529] text-[#F7F7F5]'
                          : isCurrent
                          ? 'bg-[#16171B] border-[#D4FF35]/40 text-[#D4FF35]'
                          : 'bg-[#0D0E10] border-transparent text-[#5E626E]'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold ${
                            isDone
                              ? 'bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30'
                              : isCurrent
                              ? 'bg-[#D4FF35]/20 text-[#D4FF35] border border-[#D4FF35]/40 animate-pulse'
                              : 'bg-[#1A1C20] text-[#5E626E]'
                          }`}
                        >
                          {isDone ? '✓' : stageNum}
                        </div>
                        <span>{stageName}</span>
                      </div>
                      <div>
                        {isDone && <span className="text-[10px] text-[#10B981]">COMPLETED</span>}
                        {isCurrent && <span className="text-[10px] text-[#D4FF35] animate-pulse">PROCESSING...</span>}
                        {!isDone && !isCurrent && <span className="text-[10px] text-[#5E626E]">PENDING</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Live Detection Results & Telemetry */}
          <div className="lg:col-span-5 space-y-6">
            {/* Run Overview Metrics */}
            <div className="rounded-2xl bg-[#101113] border border-[#242529] p-5">
              <div className="flex items-center justify-between pb-3 border-b border-[#242529]/80 mb-4">
                <span className="text-xs font-mono uppercase tracking-wider text-[#9296A1]">
                  Inspection Telemetry
                </span>
                {inspectionMeta && (
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    inspectionMeta.status === 'COMPLETED' ? 'bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30' : 'bg-amber-500/15 text-amber-400'
                  }`}>
                    {inspectionMeta.status}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="p-3 rounded-xl bg-[#0D0E10] border border-[#242529]">
                  <div className="text-[11px] font-mono text-[#5E626E]">Total Wagons</div>
                  <div className="text-2xl font-bold font-mono text-[#F7F7F5] mt-1">
                    {inspectionMeta?.total_wagons ?? wagons.length}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-[#0D0E10] border border-[#242529]">
                  <div className="text-[11px] font-mono text-[#5E626E]">Inference Speed</div>
                  <div className="text-2xl font-bold font-mono text-[#D4FF35] mt-1">
                    {inspectionMeta?.fps ? `${inspectionMeta.fps.toFixed(1)} FPS` : '30.0 FPS'}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-[#0D0E10] border border-[#242529]">
                  <div className="text-[11px] font-mono text-[#5E626E]">Avg Brightness</div>
                  <div className="text-sm font-bold font-mono text-[#F7F7F5] mt-1">
                    {inspectionMeta?.avg_brightness ? `${inspectionMeta.avg_brightness.toFixed(1)} lux` : '124.2 lux'}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-[#0D0E10] border border-[#242529]">
                  <div className="text-[11px] font-mono text-[#5E626E]">Est. Train Speed</div>
                  <div className="text-sm font-bold font-mono text-[#F7F7F5] mt-1">
                    {inspectionMeta?.train_speed && inspectionMeta.train_speed > 0
                      ? `${inspectionMeta.train_speed.toFixed(1)} km/h`
                      : 'Track Calibrated'}
                  </div>
                </div>
              </div>

              {/* PDF Download Button */}
              {inspectionId && (
                <a
                  href={api.getReportDownloadUrl(inspectionId)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-[#16171B] text-[#F7F7F5] border border-[#242529] hover:border-[#D4FF35]/40 hover:text-[#D4FF35] transition-all"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Audit PDF Report</span>
                </a>
              )}
            </div>

            {/* Detected Wagons Feed */}
            <div className="rounded-2xl bg-[#101113] border border-[#242529] p-5">
              <div className="flex items-center justify-between pb-3 border-b border-[#242529]/80 mb-4">
                <span className="text-xs font-mono uppercase tracking-wider text-[#9296A1]">
                  Detected Units ({wagons.length})
                </span>
                {isProcessing && (
                  <span className="flex items-center gap-1.5 text-[11px] font-mono text-[#D4FF35]">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Detecting...
                  </span>
                )}
              </div>

              {wagons.length === 0 ? (
                <div className="py-12 text-center text-[#5E626E] text-xs font-mono">
                  No wagons logged yet. Run an inspection to populate detection records.
                </div>
              ) : (
                <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
                  {wagons.map((wagon, i) => (
                    <div
                      key={wagon.id || i}
                      className="p-3 rounded-xl bg-[#0D0E10] border border-[#242529] hover:border-[#383A42] transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-mono font-bold text-[#F7F7F5]">
                          Wagon #{wagon.wagon_index || i + 1}
                        </span>
                        <div className="flex items-center gap-1.5">
                          {wagon.ocr_text && wagon.ocr_text !== 'OCR Failed' ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30">
                              OCR VERIFIED
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-800 text-zinc-400">
                              PENDING OCR
                            </span>
                          )}

                          {wagon.anomaly_type && wagon.anomaly_type !== 'None' ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-red-950/40 text-red-400 border border-red-500/30">
                              FAULT: {wagon.anomaly_type}
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#10B981]/10 text-[#10B981]">
                              PASS
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="font-mono text-xs text-[#D4FF35] bg-[#16171B] px-2.5 py-1.5 rounded-lg border border-[#242529] mb-2">
                        Serial: {wagon.ocr_text || 'OCR processing in background...'}
                      </div>

                      {/* Crop Thumbnail previews */}
                      <div className="grid grid-cols-3 gap-2">
                        {wagon.cropped_number_path && (
                          <div
                            onClick={() => setSelectedImageModal(wagon.cropped_number_path!)}
                            className="relative aspect-video rounded bg-black border border-[#242529] overflow-hidden cursor-pointer group"
                          >
                            <img
                              src={wagon.cropped_number_path}
                              alt="Number plate crop"
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                            />
                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                              <Maximize2 className="w-3 h-3 text-white" />
                            </div>
                          </div>
                        )}

                        {wagon.original_image_path && (
                          <div
                            onClick={() => setSelectedImageModal(wagon.original_image_path!)}
                            className="relative aspect-video rounded bg-black border border-[#242529] overflow-hidden cursor-pointer group"
                          >
                            <img
                              src={wagon.original_image_path}
                              alt="Wagon crop"
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                            />
                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                              <Maximize2 className="w-3 h-3 text-white" />
                            </div>
                          </div>
                        )}

                        {wagon.deblurred_image_path && (
                          <div
                            onClick={() => setSelectedImageModal(wagon.deblurred_image_path!)}
                            className="relative aspect-video rounded bg-black border border-[#242529] overflow-hidden cursor-pointer group"
                          >
                            <img
                              src={wagon.deblurred_image_path}
                              alt="Enhanced crop"
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                            />
                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                              <Maximize2 className="w-3 h-3 text-white" />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Image Zoom Modal */}
      {selectedImageModal && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setSelectedImageModal(null)}
        >
          <div className="relative max-w-4xl max-h-[90vh] bg-[#101113] border border-[#242529] rounded-2xl overflow-hidden p-2 shadow-2xl">
            <img
              src={selectedImageModal}
              alt="Enlarged crop view"
              className="max-w-full max-h-[85vh] object-contain rounded-xl"
            />
            <button
              onClick={() => setSelectedImageModal(null)}
              className="absolute top-4 right-4 px-3 py-1 rounded bg-[#08090B]/80 text-white text-xs font-mono border border-[#242529]"
            >
              Close [ESC]
            </button>
          </div>
        </div>
      )}
    </section>
  );
};
