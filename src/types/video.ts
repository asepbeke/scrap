export interface VideoItem {
  id: number;
  title?: string;
  display_title: string;
  thumbnail?: string;
  thumbnail_url?: string;
  videoUrl?: string;
  video_url: string;
  sourceUrl?: string;
  source_url?: string;
  category?: string;
  duration?: string;
  duration_seconds?: number;
  post_id?: string;
  username: string;
  post_title?: string;
  image_url?: string;
  embed_url: string;
  direct_url: string;
  provider: 'vidara.to' | 'vidara.so' | 'dood.to' | string;
  link_name?: string;
  source_page?: string;
  forum_page?: string;
  thread_key?: string;
  thread_name?: string;
  quality?: '4K UHD' | '1080p FHD' | '720p HD' | string;
  views?: string;
  rating?: string;
  year?: number;
  genre?: string;
  progressPercent?: number;
  progressTime?: string;
}

export interface ThreadConfig {
  id: string;
  name: string;
  thread_id: string;
  base_url: string;
  default_page: number;
  db_file: string;
  csv_file: string;
  icon: string;
  badge_color: string;
}

export interface StreamStats {
  total: number;
  is_live: boolean;
  last_error: string;
  threads: Record<string, ThreadConfig>;
  active_thread: string;
}

export interface ApiResponse<T> {
  status: 'success' | 'error' | 'live' | 'cached';
  message?: string;
  data?: T;
  total?: number;
  offset?: number;
  limit?: number;
  videos?: VideoItem[];
  video?: VideoItem;
  related?: VideoItem[];
  prev_video?: VideoItem | null;
  next_video?: VideoItem | null;
}

