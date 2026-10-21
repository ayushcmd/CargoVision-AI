import React, { useState, useEffect, useRef } from 'react';
import { X, Send, Database, Sparkles, Loader2, Image as ImageIcon, ChevronDown, ChevronUp, Layout } from 'lucide-react';
import { API_BASE_URL } from '../config/api';

interface AISearchProps {
    isOpen: boolean;
    onClose: () => void;
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
    sql?: string;
    results?: any[];
    images?: string[];
    isError?: boolean;
}

const AISearch: React.FC<AISearchProps> = ({ isOpen, onClose }) => {
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [allImages, setAllImages] = useState<string[]>([]);

    const inputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const imageEndRef = useRef<HTMLDivElement>(null);

    // Auto-focus input on open
    useEffect(() => {
        if (isOpen && inputRef.current) {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [isOpen]);

    // Auto-scroll to bottom of chat
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    // Extract images when messages change
    useEffect(() => {
        const imgs: string[] = [];
        messages.forEach(msg => {
            if (msg.images) imgs.push(...msg.images);
        });
        // Deduplicate
        const uniqueImgs = Array.from(new Set(imgs));
        setAllImages(uniqueImgs);

        // Scroll to bottom of images if new ones added
        if (uniqueImgs.length > 0) {
            setTimeout(() => imageEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 300);
        }
    }, [messages]);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim() || isLoading) return;

        const userQuery = query.trim();
        setQuery('');

        // Add user message
        setMessages(prev => [...prev, { role: 'user', content: userQuery }]);
        setIsLoading(true);

        try {
            const response = await fetch(`${API_BASE_URL}/api/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userQuery })
            });

            const data = await response.json();

            if (data.error) {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: "I encountered an error trying to process that.",
                    isError: true
                }]);
            } else {
                // Extract images from results
                const images: string[] = [];
                if (data.results && Array.isArray(data.results)) {
                    const imageKeys = ['original_image_path', 'deblurred_image_path', 'cropped_number_path', 'anomaly_image_path'];
                    data.results.forEach((row: any) => {
                        Object.entries(row).forEach(([key, val]: [string, any]) => {
                            // Check if it's a known image column or looks like an image URL
                            if (typeof val === 'string' && val.startsWith('http')) {
                                const isImageKey = imageKeys.includes(key);
                                const isImageUrl = val.includes('.jpg') || val.includes('.png') || val.includes('.jpeg') || val.includes('.webp');
                                if (isImageKey || isImageUrl) {
                                    if (!images.includes(val)) images.push(val);
                                }
                            }
                        });
                    });
                }

                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: data.answer || "Here are the results I found.",
                    sql: data.sql,
                    results: data.results,
                    images: images.length > 0 ? images : undefined
                }]);
            }
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "Failed to connect to the server. Please check your connection.",
                isError: true
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] bg-[#050505] animate-in fade-in duration-200 flex flex-col">
            {/* Header */}
            <div className="w-full border-b border-white/10 bg-[#0a0a0a]/80 backdrop-blur-md z-20">
                <div className="max-w-[1920px] mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg shadow-lg shadow-purple-900/20">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight">Data Intelligence AI</h2>
                        </div>
                    </div>

                    <button
                        onClick={onClose}
                        className="p-2.5 hover:bg-white/10 rounded-full text-zinc-400 hover:text-white transition-all duration-200 border border-transparent hover:border-white/10"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>
            </div>

            {/* Split Screen Container */}
            <div className="flex-1 overflow-hidden flex flex-row">

                {/* LEFT PANEL: Chat Interface (60%) */}
                <div className="flex-[3] flex flex-col border-r border-white/5 bg-gradient-to-b from-[#0a0a0a] to-[#050505] relative">
                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6 custom-scrollbar">
                        {messages.length === 0 && (
                            <div className="h-full flex flex-col items-center justify-center text-zinc-500 space-y-8 animate-in slide-in-from-bottom-5 duration-500">
                                <div className="w-20 h-20 bg-white/5 rounded-3xl flex items-center justify-center border border-white/5">
                                    <Layout className="w-10 h-10 text-purple-400 opacity-80" />
                                </div>
                                <div className="text-center space-y-2">
                                    <h3 className="text-2xl font-semibold text-white">Analysis & Visual Context</h3>
                                    <p className="text-zinc-400 max-w-sm mx-auto">Chat on the left. Relevant images will appear automatically on the right.</p>
                                </div>

                                <div className="grid grid-cols-1 gap-3 w-full max-w-lg">
                                    {[
                                        "Show me the last 5 wagons with defects",
                                        "How many wagons were inspected today?",
                                        "Find anomalies in the latest video"
                                    ].map((suggestion, i) => (
                                        <button
                                            key={i}
                                            onClick={() => {
                                                setQuery(suggestion);
                                            }}
                                            className="p-4 bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 rounded-xl text-left transition-all group flex items-center justify-between"
                                        >
                                            <span className="text-zinc-200 text-sm font-medium group-hover:text-white">{suggestion}</span>
                                            <Send className="w-4 h-4 text-zinc-600 group-hover:text-purple-400 transition-colors" />
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {messages.map((msg, idx) => (
                            <ChatMessage key={idx} message={msg} />
                        ))}

                        {isLoading && (
                            <div className="flex justify-start animate-pulse">
                                <div className="bg-white/5 rounded-2xl rounded-tl-sm px-5 py-4 flex items-center gap-3 border border-white/5">
                                    <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
                                    <span className="text-sm font-medium text-zinc-300">Analyzing database & generating insights...</span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <div className="p-6 bg-[#0a0a0a] border-t border-white/10">
                        <form onSubmit={handleSearch} className="relative max-w-4xl mx-auto flex gap-3">
                            <input
                                ref={inputRef}
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Message AI Assistant..."
                                className="w-full bg-[#151515] border border-white/10 rounded-xl pl-5 pr-14 py-4 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500/30 font-medium transition-all"
                            />
                            <button
                                type="submit"
                                disabled={isLoading || !query.trim()}
                                className="p-4 bg-white text-black rounded-xl hover:bg-zinc-200 disabled:opacity-50 disabled:hover:bg-white transition-all transform active:scale-95 shadow-lg shadow-white/5"
                            >
                                <Send className="w-5 h-5" />
                            </button>
                        </form>
                    </div>
                </div>

                {/* RIGHT PANEL: Visual Context (40%) */}
                <div className="flex-[2] bg-[#080808] border-l border-white/5 flex flex-col">
                    <div className="p-4 border-b border-white/5 bg-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <ImageIcon className="w-4 h-4 text-purple-400" />
                            <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Visual Context</h3>
                        </div>
                        <span className="text-xs text-zinc-500 px-2 py-1 bg-black/40 rounded border border-white/5">{allImages.length} Images</span>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 custom-scrollbar bg-black/20">
                        {allImages.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-3">
                                <ImageIcon className="w-12 h-12 opacity-20" />
                                <p className="text-sm text-center max-w-[200px]">Images referenced in the chat will appear here automatically.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 gap-4">
                                {allImages.map((img, idx) => (
                                    <div key={idx} className="group relative rounded-xl overflow-hidden border border-white/10 bg-white/5 animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-backwards" style={{ animationDelay: `${idx * 100}ms` }}>
                                        <div className="aspect-video w-full bg-black/50 relative">
                                            <img
                                                src={img}
                                                alt={`Context ${idx}`}
                                                className="w-full h-full object-contain transition-transform duration-500 group-hover:scale-105"
                                            />
                                        </div>
                                        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity flex justify-end">
                                            <a
                                                href={img}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-xs text-white bg-white/20 hover:bg-white/30 px-3 py-1.5 rounded-full backdrop-blur-md transition-colors"
                                            >
                                                View Full Size
                                            </a>
                                        </div>
                                    </div>
                                ))}
                                <div ref={imageEndRef} />
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
};

// Helper Component for Messages
const ChatMessage: React.FC<{ message: Message }> = ({ message }) => {
    const isUser = message.role === 'user';
    const [showDetails, setShowDetails] = useState(false);

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`max-w-[85%] space-y-3 ${isUser
                    ? 'bg-purple-600 text-white rounded-2xl rounded-tr-sm shadow-lg shadow-purple-900/20'
                    : 'bg-[#1a1a1a] border border-white/10 text-zinc-100 rounded-2xl rounded-tl-sm'
                    } p-5 shadow-sm`}
            >
                {/* Main Content */}
                <div className="text-sm leading-relaxed whitespace-pre-wrap font-medium">
                    {message.content}
                </div>

                {/* Technical Details Toggle */}
                {(message.sql || message.results) && (
                    <div className={`pt-3 mt-1 border-t ${isUser ? 'border-white/20' : 'border-white/5'}`}>
                        <button
                            onClick={() => setShowDetails(!showDetails)}
                            className={`flex items-center gap-2 text-xs font-semibold ${isUser ? 'text-white/70 hover:text-white' : 'text-zinc-500 hover:text-purple-400'} transition-colors`}
                        >
                            {showDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            {showDetails ? 'Hide' : 'Show'} Data Source
                        </button>

                        {showDetails && (
                            <div className="mt-3 space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
                                {message.sql && (
                                    <div className="bg-black/30 rounded p-3 text-[10px] font-mono border border-white/5">
                                        <div className="flex items-center gap-1.5 mb-1 text-purple-400 uppercase tracking-wider font-bold">
                                            <Database className="w-3 h-3" /> SQL Executed
                                        </div>
                                        <div className="text-zinc-300 break-words">{message.sql}</div>
                                    </div>
                                )}
                                {message.results && (
                                    <div className="bg-black/30 rounded p-3 text-[10px] font-mono border border-white/5">
                                        <div className="mb-1 text-zinc-400 uppercase tracking-wider font-bold">Raw JSON Results ({message.results.length})</div>
                                        <div className="max-h-40 overflow-y-auto custom-scrollbar">
                                            <pre>{JSON.stringify(message.results, null, 2)}</pre>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AISearch;
