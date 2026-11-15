import React, { useState } from 'react';
import { Info } from 'lucide-react';
import { VideoItem } from '../types/video';
import { PlayButton, OpenSourceButton, FavoriteButton, ShareButton } from './buttons';

interface HeroSectionProps {
  featuredVideos: VideoItem[];
  onPlay: (video: VideoItem) => void;
  onDetail: (video: VideoItem) => void;
  onToggleWatchlist: (video: VideoItem) => void;
  isWatchlisted?: boolean;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  featuredVideos,
  onPlay,
  onDetail,
  onToggleWatchlist,
  isWatchlisted = false,
}) => {
  const [activeIndex, setActiveIndex] = useState<number>(0);
  const hero = featuredVideos[activeIndex] || featuredVideos[0];

  if (!hero) return null;

  const targetUrl =
    hero.videoUrl ||
    hero.video_url ||
    hero.direct_url ||
    hero.sourceUrl ||
    hero.source_url ||
    '';

  return (
    <section className="relative min-h-[640px] sm:min-h-[700px] lg:h-[750px] xl:h-[760px] flex items-center overflow-hidden -mt-6">
      {/* Background Hero Image */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        <img
          src={hero.thumbnail_url || '/static/placeholder.svg'}
          alt={hero.display_title}
          className="w-full h-full object-cover object-center filter brightness-[0.80] contrast-[1.12] saturate-[1.08] transition-all duration-700 scale-100 will-change-transform"
        />
        {/* Horizontal reading gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#080A0F] via-[#080A0F]/85 to-transparent w-full lg:w-[72%] z-10" />
        {/* Subtle right vignette */}
        <div className="absolute inset-y-0 right-0 w-36 sm:w-64 bg-gradient-to-l from-[#080A0F]/60 via-[#080A0F]/20 to-transparent z-10" />
        {/* Top vignette */}
        <div className="absolute top-0 inset-x-0 h-32 bg-gradient-to-b from-[#080A0F] via-[#080A0F]/60 to-transparent z-10" />
        {/* Bottom fade */}
        <div className="absolute bottom-0 inset-x-0 h-44 bg-gradient-to-t from-[#080A0F] via-[#080A0F]/80 to-transparent z-10" />
      </div>

      {/* Hero Ambient Glow Spheres */}
      <div className="absolute top-1/4 left-10 w-[480px] h-[480px] bg-[#8B5CF6]/15 rounded-full filter blur-[140px] pointer-events-none z-10" />
      <div className="absolute bottom-10 right-10 w-[420px] h-[420px] bg-[#3B82F6]/15 rounded-full filter blur-[130px] pointer-events-none z-10" />

      {/* Hero Content Container */}
      <div className="relative z-20 max-w-[1550px] w-full mx-auto px-4 sm:px-6 lg:px-10 py-12 lg:py-0">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          
          {/* Left Column: Video Information (55-65% width) */}
          <div className="lg:col-span-7 xl:col-span-8 space-y-5 sm:space-y-6">
            {/* Badges */}
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] text-white shadow-lg">
                ★ Featured Premiere
              </span>
              <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-[#141A27] border border-white/[0.08] text-[#94A3B8] font-mono">
                {hero.quality || '4K UHD'}
              </span>
              <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-[#141A27] border border-white/[0.08] text-slate-200 uppercase font-mono">
                {hero.provider}
              </span>
              <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-white/10 text-emerald-400 font-mono">
                {hero.rating || '4.9'} ★ Match
              </span>
              <span className="px-2.5 py-1 rounded-lg text-xs text-[#94A3B8] font-mono bg-[#141A27]/70 border border-white/[0.06]">
                ⏱ {hero.duration || '18:45'}
              </span>
            </div>

            {/* Title (56-72px on large desktop) */}
            <h1 className="font-extrabold text-3xl sm:text-5xl lg:text-6xl xl:text-[68px] text-[#F8FAFC] tracking-tight leading-[1.08] max-w-3xl drop-shadow-2xl line-clamp-2">
              {hero.display_title}
            </h1>

            {/* Synopsis */}
            <p className="text-sm sm:text-base lg:text-lg text-[#94A3B8] max-w-2xl leading-relaxed line-clamp-2 sm:line-clamp-3">
              Konten video eksklusif diunggah oleh <strong>@{hero.username}</strong> di {hero.thread_name || 'StreamVault'}. Nikmati pemutaran video beresolusi tinggi dengan audio jernih dan kontrol pemutar bioskop modern.
            </p>

            {/* Premium Action Button Group */}
            <div className="flex items-center gap-3.5 pt-2 flex-wrap">
              <PlayButton
                onClick={() => onPlay(hero)}
                label="Watch Now"
                variant="large"
              />

              <OpenSourceButton
                url={targetUrl}
                label="Open Source"
                className="h-12 px-6 rounded-full"
              />

              <button
                onClick={() => onDetail(hero)}
                className="h-12 px-5 rounded-full bg-white/[0.08] hover:bg-white/[0.16] backdrop-blur-md border border-white/10 text-slate-100 hover:text-white font-bold text-xs sm:text-sm transition-all flex items-center gap-2 shadow-md"
                title="Lihat Detail Video"
              >
                <Info className="w-4 h-4 text-[#8B5CF6]" />
                <span>Detail Video</span>
              </button>

              <FavoriteButton
                isFavorite={isWatchlisted}
                onToggle={() => onToggleWatchlist(hero)}
              />

              <ShareButton
                url={targetUrl}
                title={hero.display_title}
              />
            </div>

            {/* Carousel Slide Indicators */}
            {featuredVideos.length > 1 && (
              <div className="flex items-center gap-2 pt-2 sm:pt-4">
                <span className="text-[11px] font-bold text-[#94A3B8] uppercase tracking-wider mr-2">Sorotan:</span>
                {featuredVideos.slice(0, 5).map((fVid, idx) => (
                  <button
                    key={fVid.id}
                    onClick={() => setActiveIndex(idx)}
                    className={`h-1.5 rounded-full transition-all duration-300 ${
                      idx === activeIndex ? 'w-8 bg-[#8B5CF6]' : 'w-3 bg-white/20 hover:bg-white/40'
                    }`}
                    title={fVid.display_title}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Right Column: Featured Video Preview Poster Card (35-45% width) */}
          <div className="hidden lg:flex lg:col-span-5 xl:col-span-4 justify-center items-center">
            <div className="relative w-full max-w-md group cursor-pointer" onClick={() => onDetail(hero)}>
              <div className="absolute -inset-2 bg-gradient-to-r from-[#8B5CF6]/30 to-[#3B82F6]/30 rounded-3xl blur-2xl opacity-60 group-hover:opacity-90 transition-opacity duration-500" />
              <div className="relative rounded-2xl overflow-hidden bg-[#141A27] border border-white/15 shadow-2xl transition-all duration-500 group-hover:scale-[1.03] group-hover:border-[#8B5CF6]/50">
                <div className="relative aspect-video overflow-hidden bg-[#0D111B]">
                  <img
                    src={hero.thumbnail_url || '/static/placeholder.svg'}
                    alt={hero.display_title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#080A0F] via-transparent to-transparent" />
                  <div className="absolute top-3 left-3 right-3 flex items-center justify-between z-10">
                    <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-[#141A27]/90 text-white font-mono border border-white/15">
                      {hero.quality || '4K UHD'}
                    </span>
                    <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-[#8B5CF6]/90 text-white font-mono uppercase tracking-wider shadow-sm">
                      {hero.provider}
                    </span>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center z-20">
                    <div className="w-14 h-14 rounded-full bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                      <PlayButton variant="circular" onClick={() => onPlay(hero)} />
                    </div>
                  </div>
                  <span className="absolute bottom-3 right-3 px-2.5 py-1 rounded text-xs font-mono font-bold bg-black/80 text-white border border-white/15 z-10">
                    {hero.duration || '18:45'}
                  </span>
                </div>
                <div className="p-4 space-y-1 bg-[#141A27]">
                  <div className="flex items-center justify-between text-[11px] text-[#94A3B8]">
                    <span className="uppercase tracking-wider font-bold text-[#8B5CF6]">Featured Choice</span>
                    <span className="font-mono text-emerald-400 font-bold">{hero.rating || '4.9'} ★</span>
                  </div>
                  <h3 className="text-sm font-bold text-[#F8FAFC] truncate group-hover:text-purple-300 transition-colors">
                    {hero.display_title}
                  </h3>
                  <p className="text-[11px] text-[#94A3B8] flex items-center justify-between pt-1">
                    <span>@{hero.username}</span>
                    <span className="text-[#3B82F6] hover:underline">Klik untuk preview &rarr;</span>
                  </p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
  );
};
