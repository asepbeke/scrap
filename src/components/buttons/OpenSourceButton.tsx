import React from 'react';
import { ExternalLink } from 'lucide-react';
import { VideoActionButton } from './VideoActionButton';

export interface OpenSourceButtonProps {
  url?: string;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  variant?: 'pill' | 'circular' | 'compact';
  label?: string;
  className?: string;
  disabled?: boolean;
}

export const OpenSourceButton: React.FC<OpenSourceButtonProps> = ({
  url,
  onClick,
  variant = 'pill',
  label = 'Open Source',
  className = '',
  disabled = false,
}) => {
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    e.preventDefault();

    if (onClick) {
      onClick(e);
      return;
    }

    if (!url) return;

    try {
      const parsed = new URL(url, window.location.href);
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        window.open(parsed.href, '_blank', 'noopener,noreferrer');
      } else {
        console.warn('Blocked unsafe URL scheme:', parsed.protocol);
      }
    } catch (err) {
      console.error('Invalid URL for open in new tab:', err);
    }
  };

  const isAccessibleDisabled = disabled || !url;

  if (variant === 'circular') {
    return (
      <VideoActionButton
        onClick={handleClick}
        variant="icon-glass"
        disabled={isAccessibleDisabled}
        tooltip="Open original source in new tab"
        className={`group ${className}`}
      >
        <ExternalLink className="w-4 h-4 text-[#94A3B8] group-hover:text-[#F8FAFC] group-hover:scale-105 transition-all duration-300" />
      </VideoActionButton>
    );
  }

  if (variant === 'compact') {
    return (
      <VideoActionButton
        onClick={handleClick}
        variant="glass"
        size="sm"
        disabled={isAccessibleDisabled}
        tooltip="Open original source in new tab"
        className={`group gap-1.5 px-3.5 py-1.5 min-h-[44px] sm:min-h-[36px] ${className}`}
      >
        <ExternalLink className="w-3.5 h-3.5 text-[#94A3B8] group-hover:text-[#F8FAFC] transition-colors duration-300" />
        <span className="text-xs text-[#F8FAFC] font-medium">{label}</span>
      </VideoActionButton>
    );
  }

  return (
    <VideoActionButton
      onClick={handleClick}
      variant="glass"
      size="md"
      disabled={isAccessibleDisabled}
      tooltip="Open original source in new tab"
      className={`group gap-2 px-5 py-2.5 min-h-[44px] ${className}`}
    >
      <ExternalLink className="w-4 h-4 text-[#94A3B8] group-hover:text-[#F8FAFC] transition-colors duration-300" />
      <span className="text-xs sm:text-sm font-semibold tracking-wide text-[#F8FAFC]">{label}</span>
    </VideoActionButton>
  );
};
