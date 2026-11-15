import { VideoItem, ApiResponse, ThreadConfig } from '../types/video';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000/api';

export async function fetchVideos(params: {
  thread?: string;
  page?: number;
  provider?: string;
  q?: string;
  limit?: number;
  offset?: number;
  sort?: string;
} = {}): Promise<{ videos: VideoItem[]; total: number }> {
  const query = new URLSearchParams();
  if (params.thread) query.append('thread', params.thread);
  if (params.page) query.append('page', params.page.toString());
  if (params.provider) query.append('provider', params.provider);
  if (params.q) query.append('q', params.q);
  if (params.limit) query.append('limit', params.limit.toString());
  if (params.offset) query.append('offset', params.offset.toString());
  if (params.sort) query.append('sort', params.sort);

  const res = await fetch(`${API_BASE}/videos?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch videos');
  const json: ApiResponse<VideoItem[]> = await res.json();
  return {
    videos: json.videos || [],
    total: json.total || 0,
  };
}

export async function fetchVideoDetail(id: number): Promise<{
  video: VideoItem;
  related: VideoItem[];
  prev_video: VideoItem | null;
  next_video: VideoItem | null;
}> {
  const res = await fetch(`${API_BASE}/video/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch video #${id}`);
  const json = await res.json();
  return {
    video: json.video,
    related: json.related || [],
    prev_video: json.prev_video || null,
    next_video: json.next_video || null,
  };
}

export async function searchVideos(query: string): Promise<VideoItem[]> {
  if (!query.trim()) return [];
  const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error('Search failed');
  const json = await res.json();
  return json.results || [];
}

export async function fetchThreads(): Promise<{
  threads: Record<string, ThreadConfig>;
  active_thread: string;
}> {
  const res = await fetch(`${API_BASE}/threads`);
  if (!res.ok) throw new Error('Failed to fetch threads');
  const json = await res.json();
  return {
    threads: json.threads,
    active_thread: json.active_thread,
  };
}

