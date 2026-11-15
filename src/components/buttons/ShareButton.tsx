import React, { useState } from 'react';
import { Share2, Check } from 'lucide-react';
import { VideoActionButton } from './VideoActionButton';

export interface ShareButtonProps {
  url?: string;
  title?: string;
  onShare?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
  disabled?: boolean;
}

export const ShareButton: React.FC<ShareButtonProps> = ({
  url,
  title = 'StreamVault Video',
  onShare,
  className = '',
  disabled = false,
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  const handleShare = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    e.preventDefault();

    if (onShare) {
      onShare(e);
      return;
    }

    const shareUrl = url || (typeof window !== 'undefined' ? window.location.href : '');

    if (navigator.share && /mobile|android|iphone/i.test(navigator.userAgent)) {
      try {
        await navigator.share({
          title,
          url: shareUrl,
        });
        return;
      } catch {
        // Fallback to clipboard copy
      }
    }

    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  return (
    <VideoActionButton
      onClick={handleShare}
      variant="tertiary"
      disabled={disabled}
      tooltip={copied ? 'Link Copied!' : 'Share Video'}
      className={`group ${className}`}
    >
      {copied ? (
        <Check className="w-4 h-4 text-emerald-400 scale-110 transition-transform duration-200" />
      ) : (
        <Share2 className="w-4 h-4 text-[#94A3B8] group-hover:text-[#F8FAFC] group-hover:scale-105 transition-all duration-300" />
      )}
    </VideoActionButton>
  );
};
