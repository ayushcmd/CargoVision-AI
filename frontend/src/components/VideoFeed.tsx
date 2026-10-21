import React from 'react';
import { API_BASE_URL } from '../config/api';

interface VideoFeedProps {
    streamId: number;
}

const VideoFeed: React.FC<VideoFeedProps> = ({ streamId }) => {
    const [isProcessing, setIsProcessing] = React.useState(false);

    const toggleProcessing = async () => {
        try {
            if (isProcessing) {
                await fetch(`${API_BASE_URL}/live/stop`, { method: 'POST' });
                setIsProcessing(false);
            } else {
                await fetch(`${API_BASE_URL}/live/start?stream_id=${streamId}`, { method: 'POST' });
                setIsProcessing(true);
            }
        } catch (error) {
            console.error("Failed to toggle processing:", error);
        }
    };

    // Check status on mount
    React.useEffect(() => {
        fetch(`${API_BASE_URL}/live/status`)
            .then(res => res.json())
            .then(data => {
                if (data.is_running) setIsProcessing(true);
            })
            .catch(console.error);
    }, []);

    return (
        <div className="relative w-full h-full bg-black">
            {/* Live Indicator */}
            <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-full border border-zinc-700">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-xs font-mono text-red-400">LIVE</span>
            </div>

            {/* Overlay Information & Controls */}
            <div className="absolute top-4 right-4 z-10 flex flex-col items-end gap-2">
                {/* Processing Toggle */}
                <button
                    onClick={toggleProcessing}
                    className={`
                        flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold tracking-wide transition-all
                        ${isProcessing
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50 hover:bg-amber-500/30'
                            : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500/30'}
                    `}
                >
                    <div className={`w-2 h-2 rounded-full ${isProcessing ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`} />
                    {isProcessing ? 'STOP AI' : 'START AI'}
                </button>
            </div>

            {/* Video Stream - always rendered */}
            <img
                src={`${API_BASE_URL}/video_feed/${streamId}`}
                alt={`Stream ${streamId}`}
                className="w-full h-full object-fill"
            />

            {/* Processing Overlay (Active State) */}
            {isProcessing && (
                <div className="absolute inset-0 pointer-events-none border-2 border-blue-500/40 animate-pulse">
                    <div className="absolute bottom-10 left-1/2 -translate-x-1/2 bg-black/70 backdrop-blur-md px-6 py-2 rounded-full border border-blue-500/50 flex items-center gap-3">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
                        <span className="text-xs font-bold text-blue-300">AI PIPELINE ACTIVE • DETECTING WAGONS</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default VideoFeed;