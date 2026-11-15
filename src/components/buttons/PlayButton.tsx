import React from 'react';
import { Play } from 'lucide-react';
import { VideoActionButton } from './VideoActionButton';

export interface PlayButtonProps {
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  variant?: 'pill' | 'circular' | 'large';
  label?: string;
  className?: string;
  disabled?: boolean;
}

export const PlayButton: React.FC<PlayButtonProps> = ({
  onClick,
  variant = 'pill',
  label = 'Putar Sekarang',
  className = '',
  disabled = false,
}) => {
  if (variant === 'circular') {
    return (
      <VideoActionButton
        onClick={onClick}
        variant="card-play"
        disabled={disabled}
        tooltip={label}
        className={`group ${className}`}
      >
        <Play className="w-5 h-5 text-white fill-white ml-0.5 group-hover:scale-110 transition-transform duration-300" />
      </VideoActionButton>
    );
  }

  return (
    <VideoActionButton
      onClick={onClick}
      variant="primary"
      size={variant === 'large' ? 'lg' : 'md'}
      disabled={disabled}
      tooltip={label}
      glow={true}
      className={`group gap-2.5 ${className}`}
    >
      <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
        <Play className="w-3.5 h-3.5 text-white fill-white ml-0.5" />
      </div>
      <span className="tracking-wide">{label}</span>
    </VideoActionButton>
  );
};

