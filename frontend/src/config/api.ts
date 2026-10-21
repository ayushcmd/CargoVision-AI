// CargoVision AI - Centralized API Service Configuration

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface Inspection {
  id: number;
  video_name: string;
  timestamp: string;
  total_wagons: number;
  enhanced_video_path?: string | null;
  status: 'PROCESSING' | 'COMPLETED' | 'FAILED' | string;
  fps?: number | null;
  resolution?: string | null;
  avg_brightness?: number | null;
  blur_stats?: string | null;
  train_speed?: number | null;
  start_time?: string | null;
  end_time?: string | null;
}

export interface WagonDetail {
  id: number;
  wagon_index: number;
  ocr_text: string;
  ocr_confidence?: number;
  original_image_path?: string;
  deblurred_image_path?: string;
  cropped_number_path?: string;
  anomaly_image_path?: string;
  anomaly_type?: string;
  anomaly_conf?: number;
  defects?: string;
  is_night?: boolean;
  timestamp?: string;
}

export interface AnalyticsDataPoint {
  date: string;
  trains: number;
  wagons: number;
  defects: number;
  night_defects: number;
  day_defects: number;
}

export interface SystemStats {
  total_wagons: number;
  last_wagon_id: string;
  defects_found: number;
  status: string;
}

export interface UploadResponse {
  message: string;
  filename: string;
  inspection_id: number;
  status: string;
}

export const api = {
  getHealth: async (): Promise<{ status: string; service: string; version: string }> => {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  },

  getHistory: async (): Promise<Inspection[]> => {
    const res = await fetch(`${API_BASE_URL}/history`);
    if (!res.ok) throw new Error(`Failed to fetch history: ${res.statusText}`);
    return res.json();
  },

  getInspectionDetails: async (id: number): Promise<WagonDetail[]> => {
    const res = await fetch(`${API_BASE_URL}/history/${id}`);
    if (!res.ok) throw new Error(`Failed to fetch inspection #${id}: ${res.statusText}`);
    return res.json();
  },

  getInspectionStatus: async (id: number): Promise<{ status: string }> => {
    const res = await fetch(`${API_BASE_URL}/inspections/${id}/status`);
    if (!res.ok) throw new Error(`Failed to fetch status for #${id}: ${res.statusText}`);
    return res.json();
  },

  uploadVideo: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Upload failed with status ${res.status}`);
    }
    return res.json();
  },

  getAnalytics: async (): Promise<AnalyticsDataPoint[]> => {
    const res = await fetch(`${API_BASE_URL}/api/analytics`);
    if (!res.ok) throw new Error(`Failed to fetch analytics: ${res.statusText}`);
    return res.json();
  },

  getStats: async (): Promise<SystemStats> => {
    const res = await fetch(`${API_BASE_URL}/stats`);
    if (!res.ok) throw new Error(`Failed to fetch stats: ${res.statusText}`);
    return res.json();
  },

  getReportDownloadUrl: (id: number): string => `${API_BASE_URL}/history/${id}/report`,
  getProcessingStreamUrl: (id: number): string => `${API_BASE_URL}/stream/processing/${id}`,
  getVideoFeedUrl: (streamId: number): string => `${API_BASE_URL}/video_feed/${streamId}`,
};
