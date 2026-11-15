import { VideoItem } from '../types/video';

const WATCHLIST_KEY = 'streamvault_watchlist';
const HISTORY_KEY = 'streamvault_history';

export interface StreamState {
  watchlist: VideoItem[];
  history: VideoItem[];
  activeModalVideo: VideoItem | null;
  isTheaterMode: boolean;
  activeThread: string;
}

export function loadStoredWatchlist(): VideoItem[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem(WATCHLIST_KEY) || '[]');
  } catch {
    return [];
  }
}

export function saveStoredWatchlist(items: VideoItem[]) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(items));
}

export function loadStoredHistory(): VideoItem[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
  } catch {
    return [];
  }
}

export function saveStoredHistory(items: VideoItem[]) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, 20)));
}

