import React from 'react';
import { ThreadConfig } from '../types/video';

interface NavbarProps {
  activeThread: string;
  threads: Record<string, ThreadConfig>;
  isLive: boolean;
  watchlistCount: number;
  onOpenSearch: () => void;
  onOpenWatchlist: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeThread,
  threads,
  isLive,
  watchlistCount,
  onOpenSearch,
  onOpenWatchlist,
}) => {
  return (
    <header className="sticky top-0 z-40 bg-[#080A0F]/80 backdrop-blur-xl border-b border-white/5 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20 gap-4">
          
          {/* Logo & Navigation */}
          <div className="flex items-center gap-6 sm:gap-8">
            <a href="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#8B5CF6] via-purple-600 to-[#06B6D4] p-0.5 shadow-lg group-hover:scale-105 transition-transform flex items-center justify-center">
                <div className="w-full h-full bg-[#080A0F] rounded-[10px] flex items-center justify-center">
                  <span className="text-transparent bg-clip-text bg-gradient-to-tr from-[#8B5CF6] to-[#06B6D4] font-bold text-sm pl-0.5">
                    ▶
                  </span>
                </div>
              </div>
              <div className="flex flex-col">
                <span className="font-extrabold text-xl sm:text-2xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent group-hover:to-[#06B6D4] transition-all">
                  Stream<span className="text-[#8B5CF6]">Vault</span>
                </span>
                <span className="text-[9px] font-mono tracking-widest text-[#06B6D4] uppercase font-bold -mt-1 hidden sm:block">
                  Next-Gen Cinema
                </span>
              </div>
            </a>

            <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
              <a href="/" className="px-3.5 py-2 rounded-lg text-white font-semibold hover:bg-white/5 transition">
                Home
              </a>
              <button
                onClick={onOpenWatchlist}
                className="px-3.5 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/5 transition flex items-center gap-2"
              >
                <span>♥</span>
                <span>Watchlist</span>
                {watchlistCount > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-rose-500 text-white font-mono">
                    {watchlistCount}
                  </span>
                )}
              </button>
            </nav>
          </div>

          {/* Right Controls: Search & Live Badge */}
          <div className="flex items-center gap-3">
            <button
              onClick={onOpenSearch}
              className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-[#11151D] hover:bg-[#171C27] border border-white/10 text-[#9CA3AF] hover:text-white text-xs transition"
            >
              <span>🔍</span>
              <span className="hidden sm:inline font-medium">Cari video...</span>
              <kbd className="hidden md:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono bg-[#080A0F] text-slate-400 border border-white/10">
                Ctrl+K
              </kbd>
            </button>

            <div className="hidden sm:flex items-center">
              {isLive ? (
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  <span className="font-mono text-[11px]">LIVE CDP</span>
                </div>
              ) : (
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/25">
                  <span className="font-mono text-[11px]">ARCHIVE DB</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

