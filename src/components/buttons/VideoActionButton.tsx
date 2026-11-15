import React from 'react';

export interface VideoActionButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'glass' | 'tertiary' | 'icon-glass' | 'secondary' | 'card-play';
  size?: 'sm' | 'md' | 'lg';
  tooltip?: string;
  glow?: boolean;
}

export const VideoActionButton: React.FC<VideoActionButtonProps> = ({
  children,
  className = '',
  variant = 'glass',
  size = 'md',
  tooltip,
  glow = false,
  type = 'button',
  disabled,
  ...props
}) => {
  const baseStyles = 'relative inline-flex items-center justify-center font-bold transition-all duration-300 select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-[#8B5CF6] disabled:opacity-40 disabled:cursor-not-allowed';

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 rounded-xl min-h-[36px]',
    md: 'text-xs sm:text-sm px-4 py-2.5 rounded-full min-h-[44px]',
    lg: 'text-sm sm:text-base px-6 py-3.5 rounded-full min-h-[48px]',
  };

  const variantStyles = {
    // Primary: Dominant PLAY action with purple-to-blue gradient
    primary:
      'bg-gradient-to-r from-[#8B5CF6] via-indigo-600 to-[#3B82F6] text-white shadow-[0_4px_20px_rgba(139,92,246,0.35)] hover:shadow-[0_6px_26px_rgba(139,92,246,0.5)] hover:scale-[1.04] active:scale-[0.97]',
    // Secondary: OPEN SOURCE with premium translucent glassmorphism
    glass:
      'bg-white/[0.06] hover:bg-white/[0.12] backdrop-blur-[16px] border border-white/[0.08] hover:border-white/[0.18] text-[#F8FAFC] shadow-sm hover:shadow-black/40 hover:scale-[1.02] active:scale-[0.98]',
    // Tertiary: Minimalist transparent icon button
    tertiary:
      'w-11 h-11 min-w-[44px] min-h-[44px] p-0 rounded-full bg-transparent hover:bg-white/[0.06] border border-transparent hover:border-white/[0.08] text-[#94A3B8] hover:text-[#F8FAFC] hover:scale-105 active:scale-95 transition-all',
    'icon-glass':
      'w-11 h-11 min-w-[44px] min-h-[44px] p-0 rounded-full bg-white/[0.06] hover:bg-white/[0.12] backdrop-blur-[16px] border border-white/[0.08] hover:border-white/[0.18] text-[#94A3B8] hover:text-[#F8FAFC] hover:scale-105 active:scale-95 shadow-sm',
    secondary:
      'bg-[#141A27] hover:bg-[#1B2232] text-[#94A3B8] hover:text-[#F8FAFC] border border-white/[0.08] hover:border-white/[0.16]',
    'card-play':
      'w-12 h-12 min-w-[44px] min-h-[44px] rounded-full bg-gradient-to-tr from-[#8B5CF6] via-indigo-600 to-[#3B82F6] text-white shadow-[0_4px_20px_rgba(139,92,246,0.4)] hover:scale-110 active:scale-95 hover:shadow-[0_6px_26px_rgba(139,92,246,0.6)]',
  };

  const glowStyle = glow ? 'shadow-[0_4px_24px_rgba(139,92,246,0.4)]' : '';

  const isIconVariant = variant === 'icon-glass' || variant === 'tertiary' || variant === 'card-play';

  return (
    <button
      type={type}
      disabled={disabled}
      title={tooltip}
      aria-label={tooltip}
      className={`${baseStyles} ${isIconVariant ? '' : sizeStyles[size]} ${variantStyles[variant]} ${glowStyle} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
