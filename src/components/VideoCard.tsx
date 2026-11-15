import React from 'react';
import { VideoItem } from '../types/video';
import { PlayButton, OpenSourceButton, FavoriteButton } from './buttons';

interface VideoCardProps {
  video: VideoItem;
  onSelect?: (video: VideoItem) => void;
  onToggleWatchlist?: (video: VideoItem) => void;
  isWatchlisted?: boolean;
}

export const VideoCard: React.FC<VideoCardProps> = ({
  video,
  onSelect,
  onToggleWatchlist,
  isWatchlisted = false,
}) => {
  const targetUrl =
    video.videoUrl ||
    video.video_url ||
    video.direct_url ||
    video.sourceUrl ||
    video.source_url ||
    '';

  return (
    <div
      onClick={() => onSelect?.(video)}
      className="group relative rounded-2xl overflow-hidden bg-[#141A27] border border-white/[0.08] hover:border-[#8B5CF6]/50 shadow-lg hover:shadow-2xl hover:-translate-y-1.5 transition-all duration-300 cursor-pointer flex flex-col justify-between"
    >
      {/* Thumbnail aspect container (16:9) with hover zoom */}
      <div className="relative aspect-video overflow-hidden bg-[#0D111B]">
        <img
          src={video.thumbnail || video.thumbnail_url || '/static/placeholder.svg'}
          alt={video.title || video.display_title}
          loading="lazy"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#141A27] via-transparent to-transparent pointer-events-none" />

        {/* Top Badges & Mobile Touch Actions (Min 44x44px for touch accessibility) */}
        <div className="absolute top-2 left-2 right-2 flex items-center justify-between z-20">
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#1B2232]/90 border border-white/[0.08] text-[#94A3B8] font-mono shadow-sm">
            {video.quality || '4K'}
          </span>

          {/* Mobile Direct Action Buttons (Always accessible without hover) */}
          <div className="flex sm:hidden items-center gap-1.5">
            <OpenSourceButton
              url={targetUrl}
              variant="circular"
              className="w-11 h-11 min-w-[44px] min-h-[44px] bg-black/70 backdrop-blur-md"
            />
            <FavoriteButton
              isFavorite={isWatchlisted}
              onToggle={() => onToggleWatchlist?.(video)}
              className="w-11 h-11 min-w-[44px] min-h-[44px] bg-black/70 backdrop-blur-md"
            />
          </div>
        </div>

        {/* Bottom Duration Badge */}
        <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#1B2232]/90 border border-white/[0.08] text-slate-200 z-10 pointer-events-none backdrop-blur-sm">
          {video.duration || '14:20'}
        </span>

        {/* Desktop Hover Action Overlay: Slide-up & Fade-in with [ ▶ Play ] [ ↗ Open Source ] */}
        <div className="hidden sm:flex absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-all duration-300 flex-col items-center justify-center gap-3 z-30 p-3 backdrop-blur-[2px]">
          <div className="flex items-center gap-3 transform translate-y-3 group-hover:translate-y-0 opacity-0 group-hover:opacity-100 transition-all duration-300 ease-out">
            {/* Primary Action: Play Video */}
            <PlayButton
              variant="circular"
              onClick={() => onSelect?.(video)}
              className="shadow-glow-primary"
            />

            {/* Secondary Action: Open Source in New Tab */}
            <OpenSourceButton
              url={targetUrl}
              variant="pill"
              label="Open Source"
              className="bg-white/10 hover:bg-white/20 border-white/20 text-white shadow-lg"
            />
          </div>
        </div>
      </div>

      {/* Card Info */}
      <div className="p-3.5 space-y-2 flex-1 flex flex-col justify-between">
        <div className="space-y-1">
          <h3
            className="text-xs sm:text-sm font-bold text-[#F8FAFC] group-hover:text-purple-300 transition line-clamp-2 leading-snug"
            title={video.display_title}
          >
            {video.display_title}
          </h3>
          <p className="text-[11px] text-[#94A3B8] flex items-center gap-1.5">
            <span className="truncate">@{video.username}</span>
          </p>
        </div>

        {/* Bottom Metadata & Favorite for Desktop */}
        <div className="pt-2 border-t border-white/[0.08] flex items-center justify-between text-[10px] text-[#94A3B8]">
          <span className="uppercase font-bold text-[#3B82F6]">{video.provider}</span>
          <div className="flex items-center gap-2">
            <span className="font-mono">ID #{video.id}</span>
            <div className="hidden sm:block">
              <FavoriteButton
                isFavorite={isWatchlisted}
                onToggle={() => onToggleWatchlist?.(video)}
                className="w-7 h-7 min-w-[28px] min-h-[28px] bg-transparent border-0 hover:bg-white/10"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
