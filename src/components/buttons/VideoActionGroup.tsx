import React from 'react';
import { VideoItem } from '../../types/video';
import { PlayButton } from './PlayButton';
import { OpenSourceButton } from './OpenSourceButton';
import { FavoriteButton } from './FavoriteButton';
import { ShareButton } from './ShareButton';

export interface VideoActionGroupProps {
  video: VideoItem;
  onPlay?: (video: VideoItem) => void;
  onToggleFavorite?: (video: VideoItem) => void;
  isFavorite?: boolean;
  className?: string;
  size?: 'md' | 'lg';
  showShare?: boolean;
  showFavorite?: boolean;
  showOpenSource?: boolean;
  playLabel?: string;
}

export const VideoActionGroup: React.FC<VideoActionGroupProps> = ({
  video,
  onPlay,
  onToggleFavorite,
  isFavorite = false,
  className = '',
  size = 'md',
  showShare = true,
  showFavorite = true,
  showOpenSource = true,
  playLabel = 'Watch Now',
}) => {
  // Target URL for Open Source (uses video link first as requested)
  const targetUrl =
    video.videoUrl ||
    video.video_url ||
    video.direct_url ||
    video.sourceUrl ||
    video.source_url ||
    '';

  return (
    <div className={`flex items-center gap-3 flex-wrap sm:flex-nowrap ${className}`}>
      {/* Primary Action: Watch Now */}
      <PlayButton
        onClick={() => onPlay?.(video)}
        label={playLabel}
        variant={size === 'lg' ? 'large' : 'pill'}
        className="flex-1 sm:flex-initial min-w-[140px]"
      />

      {/* Secondary Action: Open Source in New Tab */}
      {showOpenSource && (
        <OpenSourceButton
          url={targetUrl}
          variant="pill"
          label="Open Source"
          className="flex-1 sm:flex-initial"
        />
      )}

      {/* Add to Favorites (44x44px touch target) */}
      {showFavorite && (
        <FavoriteButton
          isFavorite={isFavorite}
          onToggle={() => onToggleFavorite?.(video)}
        />
      )}

      {/* Share Video Link (44x44px touch target) */}
      {showShare && (
        <ShareButton
          url={targetUrl || (typeof window !== 'undefined' ? window.location.href : '')}
          title={video.display_title || video.title}
        />
      )}
    </div>
  );
};

