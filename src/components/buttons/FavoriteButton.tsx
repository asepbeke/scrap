import React from 'react';
import { Heart } from 'lucide-react';
import { VideoActionButton } from './VideoActionButton';

export interface FavoriteButtonProps {
  isFavorite?: boolean;
  onToggle?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  className?: string;
  disabled?: boolean;
}

export const FavoriteButton: React.FC<FavoriteButtonProps> = ({
  isFavorite = false,
  onToggle,
  className = '',
  disabled = false,
}) => {
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    e.preventDefault();
    onToggle?.(e);
  };

  return (
    <VideoActionButton
      onClick={handleClick}
      variant="tertiary"
      disabled={disabled}
      tooltip={isFavorite ? 'Remove from Favorites' : 'Add to Favorites'}
      className={`group ${className}`}
    >
      <Heart
        className={`w-4 h-4 transition-all duration-300 group-hover:scale-110 ${
          isFavorite
            ? 'text-rose-500 fill-rose-500'
            : 'text-[#94A3B8] group-hover:text-rose-400'
        }`}
      />
    </VideoActionButton>
  );
};
