import React, { useEffect, useState } from 'react';
import { API_BASE_URL } from '../config/api';

interface Stats {
    total_wagons: number;
    last_wagon_id: string;
    defects_found: number;
    status: string;
}

const StatsPanel: React.FC = () => {
    const [stats, setStats] = useState<Stats>({
        total_wagons: 0,
        last_wagon_id: 'Waiting...',
        defects_found: 0,
        status: 'Initializing'
    });

    useEffect(() => {
        const interval = setInterval(() => {
            fetch(`${API_BASE_URL}/stats`)
                .then(res => res.json())
                .then(data => setStats(data))
                .catch(err => console.error("Error fetching stats:", err));
        }, 1000); // Poll every second

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {/* Card 1: Status */}
            <div className="space-y-2">
                <div className="text-sm text-zinc-500 font-mono uppercase">System Status</div>
                <div className={`text-3xl font-bold ${stats.status === 'Processing' ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {stats.status}
                </div>
                <div className="text-xs text-zinc-600">Real-time</div>
            </div>

            {/* Card 2: Wagon Count */}
            <div className="space-y-2">
                <div className="text-sm text-zinc-500 font-mono uppercase">Wagons Counted</div>
                <div className="text-3xl font-bold text-blue-400">{stats.total_wagons}</div>
                <div className="text-xs text-zinc-600">Session Total</div>
            </div>

            {/* Card 3: Last ID */}
            <div className="space-y-2">
                <div className="text-sm text-zinc-500 font-mono uppercase">Last Wagon ID</div>
                <div className="text-3xl font-bold text-purple-400">{stats.last_wagon_id}</div>
                <div className="text-xs text-zinc-600">Latest Scanned</div>
            </div>

            {/* Card 4: Defects */}
            <div className="space-y-2">
                <div className="text-sm text-zinc-500 font-mono uppercase">Defects Detected</div>
                <div className="text-3xl font-bold text-amber-400">{stats.defects_found}</div>
                <div className="text-xs text-zinc-600">Needs Inspection</div>
            </div>
        </div>
    );
};

export default StatsPanel;
