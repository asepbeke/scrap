import React, { useEffect, useRef, useState } from 'react';
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Volume1,
  Maximize,
  Minimize,
  PictureInPicture2,
  Settings,
  RotateCcw,
  SkipBack,
  SkipForward,
} from 'lucide-react';
import { VideoItem } from '../types/video';
import { OpenSourceButton } from './buttons/OpenSourceButton';
import { VideoActionGroup } from './buttons/VideoActionGroup';

interface VideoPlayerProps {
  video: VideoItem;
  prevVideo?: VideoItem | null;
  nextVideo?: VideoItem | null;
  onNext?: () => void;
  onPrev?: () => void;
  onToggleWatchlist?: (video: VideoItem) => void;
  isWatchlisted?: boolean;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  video,
  prevVideo,
  nextVideo,
  onNext,
  onPrev,
  onToggleWatchlist,
  isWatchlisted = false,
}) => {
  const [playerMode, setPlayerMode] = useState<'embed' | 'direct' | 'native'>('embed');
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [volume, setVolume] = useState<number>(1);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const [showControls, setShowControls] = useState<boolean>(true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [isShieldStrict, setIsShieldStrict] = useState<boolean>(true);
  const [hasNativeError, setHasNativeError] = useState<boolean>(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const cinemaBoxRef = useRef<HTMLDivElement | null>(null);
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const targetUrl =
    video.videoUrl ||
    video.video_url ||
    video.direct_url ||
    video.sourceUrl ||
    video.source_url ||
    '';

  // Auto-hide floating toolbar & overlay controls
  const handleMouseMove = () => {
    setShowControls(true);
    if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
    if (isPlaying) {
      controlsTimeoutRef.current = setTimeout(() => {
        setShowControls(false);
      }, 2500);
    }
  };

  const handleMouseLeave = () => {
    if (isPlaying) {
      setShowControls(false);
    }
  };

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleVolumeChange = (newVol: number) => {
    if (!videoRef.current) return;
    videoRef.current.volume = newVol;
    setVolume(newVol);
    setIsMuted(newVol === 0);
  };

  const handleSpeedChange = (speed: number) => {
    if (!videoRef.current) return;
    videoRef.current.playbackRate = speed;
    setPlaybackSpeed(speed);
  };

  const toggleFullscreen = () => {
    const el = cinemaBoxRef.current;
    if (!el) return;
    if (!document.fullscreenElement) {
      el.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  const togglePiP = async () => {
    if (!videoRef.current) return;
    if (document.pictureInPictureElement) {
      await document.exitPictureInPicture();
    } else if (document.pictureInPictureEnabled) {
      await videoRef.current.requestPictureInPicture();
    }
  };

  const formatTime = (seconds: number) => {
    if (isNaN(seconds)) return '00:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
  };

  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFsChange);
    return () => document.removeEventListener('fullscreenchange', handleFsChange);
  }, []);

  return (
    <div className="space-y-6">
      {/* Player Mode Switcher Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#0D111B] border border-white/[0.08] rounded-2xl p-3 text-xs">
        <div className="inline-flex rounded-xl bg-[#080A0F] border border-white/[0.08] p-1">
          <button
            onClick={() => setPlayerMode('embed')}
            className={`px-3 py-1.5 rounded-lg font-bold transition ${
              playerMode === 'embed'
                ? 'bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] text-white shadow-md'
                : 'text-[#94A3B8] hover:text-white'
            }`}
          >
            Player 1 (Embed)
          </button>
          <button
            onClick={() => setPlayerMode('direct')}
            className={`px-3 py-1.5 rounded-lg font-bold transition ${
              playerMode === 'direct'
                ? 'bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] text-white shadow-md'
                : 'text-[#94A3B8] hover:text-white'
            }`}
          >
            Player 2 (Direct)
          </button>
          <button
            onClick={() => setPlayerMode('native')}
            className={`px-3 py-1.5 rounded-lg font-bold transition ${
              playerMode === 'native'
                ? 'bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] text-white shadow-md'
                : 'text-[#94A3B8] hover:text-white'
            }`}
          >
            Player 3 (HLS/MP4)
          </button>
        </div>

        <div className="flex items-center gap-2">
          <OpenSourceButton
            url={targetUrl}
            variant="compact"
            label="Open Source"
          />
          <button
            onClick={() => setIsShieldStrict(!isShieldStrict)}
            className="px-3 py-1.5 rounded-xl bg-[#141A27] text-white border border-white/[0.08] hover:border-[#8B5CF6]/50 transition text-xs font-semibold flex items-center gap-1.5"
            title="Toggle Sandbox Security Mode"
          >
            <Settings className="w-3.5 h-3.5 text-[#3B82F6]" />
            <span className="hidden sm:inline">Shield:</span>{' '}
            <span className={isShieldStrict ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
              {isShieldStrict ? 'Ketat' : 'Standar'}
            </span>
          </button>
        </div>
      </div>

      {/* Cinema Player Container with Floating Action Toolbar */}
      <div
        id="cinemaPlayerBox"
        ref={cinemaBoxRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="relative aspect-video rounded-3xl overflow-hidden border border-white/[0.08] bg-black shadow-cinema group select-none"
      >
        {/* Floating Action Toolbar on Player (Auto-hides on idle, visible on hover) */}
        <div
          className={`absolute top-4 right-4 z-40 flex items-center gap-2 p-1.5 rounded-2xl bg-[#0D111B]/80 backdrop-blur-[16px] border border-white/[0.08] shadow-2xl transition-all duration-300 ${
            showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
        >
          {/* Open Original Source */}
          <OpenSourceButton
            url={targetUrl}
            variant="compact"
            label="Open Source"
            className="h-9 px-3.5 bg-white/[0.08] hover:bg-white/[0.16] border-white/[0.08] text-white shadow-sm"
          />

          {/* Picture-in-Picture */}
          <button
            onClick={togglePiP}
            className="w-9 h-9 rounded-xl bg-white/[0.05] hover:bg-white/[0.12] text-slate-200 hover:text-white flex items-center justify-center transition border border-white/[0.08]"
            title="Picture in Picture"
          >
            <PictureInPicture2 className="w-4 h-4" />
          </button>

          {/* Fullscreen Toggle */}
          <button
            onClick={toggleFullscreen}
            className="w-9 h-9 rounded-xl bg-white/[0.05] hover:bg-white/[0.12] text-slate-200 hover:text-white flex items-center justify-center transition border border-white/[0.08]"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
          </button>

          {/* Settings / Sandbox */}
          <button
            onClick={() => setIsShieldStrict(!isShieldStrict)}
            className="w-9 h-9 rounded-xl bg-white/[0.05] hover:bg-white/[0.12] text-slate-200 hover:text-white flex items-center justify-center transition border border-white/[0.08]"
            title="Player Sandbox Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>

        {playerMode === 'embed' && (
          <iframe
            src={video.embed_url}
            title={video.display_title}
            className="w-full h-full"
            allowFullScreen
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            sandbox={isShieldStrict ? 'allow-scripts allow-same-origin allow-presentation allow-forms' : undefined}
          />
        )}

        {playerMode === 'direct' && (
          <iframe
            src={video.direct_url}
            title={video.display_title}
            className="w-full h-full"
            allowFullScreen
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          />
        )}

        {playerMode === 'native' && (
          <div className="relative w-full h-full bg-black">
            <video
              ref={videoRef}
              src={video.video_url}
              poster={video.thumbnail_url}
              className="w-full h-full object-contain cursor-pointer"
              onClick={togglePlay}
              onTimeUpdate={() => {
                if (videoRef.current) {
                  setCurrentTime(videoRef.current.currentTime);
                  setDuration(videoRef.current.duration || 0);
                }
              }}
              onError={() => setHasNativeError(true)}
            />

            {/* Big Center Play Icon */}
            {!isPlaying && (
              <button
                onClick={togglePlay}
                className="absolute inset-0 m-auto w-20 h-20 rounded-full bg-gradient-to-tr from-[#8B5CF6] to-[#3B82F6] text-white flex items-center justify-center shadow-glow-primary hover:scale-110 transition-transform backdrop-blur-sm"
              >
                <Play className="w-8 h-8 fill-white ml-1" />
              </button>
            )}

            {/* Custom Overlay Controls */}
            <div
              className={`absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black via-black/75 to-transparent transition-opacity duration-300 space-y-2.5 ${
                showControls ? 'opacity-100' : 'opacity-0 pointer-events-none'
              }`}
            >
              {/* Scrub Progress Bar */}
              <div
                className="relative w-full h-2 bg-white/20 hover:h-3 rounded-full cursor-pointer transition-all overflow-hidden"
                onClick={(e) => {
                  if (!videoRef.current || !duration) return;
                  const rect = e.currentTarget.getBoundingClientRect();
                  const pos = (e.clientX - rect.left) / rect.width;
                  videoRef.current.currentTime = pos * duration;
                }}
              >
                <div
                  className="h-full bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] rounded-full transition-all"
                  style={{ width: `${(currentTime / (duration || 1)) * 100}%` }}
                />
              </div>

              {/* Action Buttons Row */}
              <div className="flex items-center justify-between text-white text-xs pt-1">
                <div className="flex items-center gap-3">
                  <button onClick={togglePlay} className="p-1.5 rounded-lg hover:bg-white/10 font-bold transition">
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-white ml-0.5" />}
                  </button>
                  {prevVideo && onPrev && (
                    <button onClick={onPrev} className="p-1.5 rounded-lg hover:bg-white/10 text-[#94A3B8] hover:text-white transition">
                      <SkipBack className="w-4 h-4" />
                    </button>
                  )}
                  {nextVideo && onNext && (
                    <button onClick={onNext} className="p-1.5 rounded-lg hover:bg-white/10 text-[#94A3B8] hover:text-white transition">
                      <SkipForward className="w-4 h-4" />
                    </button>
                  )}
                  <div className="flex items-center gap-1.5">
                    <button onClick={toggleMute} className="p-1.5 rounded-lg hover:bg-white/10 transition">
                      {isMuted ? (
                        <VolumeX className="w-4 h-4 text-rose-400" />
                      ) : volume < 0.5 ? (
                        <Volume1 className="w-4 h-4" />
                      ) : (
                        <Volume2 className="w-4 h-4" />
                      )}
                    </button>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={isMuted ? 0 : volume}
                      onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                      className="w-16 accent-[#8B5CF6] h-1 bg-white/20 rounded cursor-pointer"
                    />
                  </div>
                  <span className="font-mono text-[11px] text-[#94A3B8]">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>

                <div className="flex items-center gap-2 font-mono">
                  <button
                    onClick={() => handleSpeedChange(playbackSpeed === 1.0 ? 1.5 : playbackSpeed === 1.5 ? 2.0 : 1.0)}
                    className="px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-[11px] font-bold"
                  >
                    {playbackSpeed}x
                  </button>
                  <button onClick={togglePiP} className="p-1.5 rounded-lg hover:bg-white/10 transition" title="Picture in Picture">
                    <PictureInPicture2 className="w-4 h-4" />
                  </button>
                  <button onClick={toggleFullscreen} className="p-1.5 rounded-lg hover:bg-white/10 transition" title="Fullscreen">
                    {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            {hasNativeError && (
              <div className="absolute inset-0 bg-[#080A0F]/90 backdrop-blur-md flex flex-col items-center justify-center p-6 text-center space-y-3 z-50">
                <div className="w-12 h-12 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center text-xl">
                  ⚠️
                </div>
                <h4 className="font-bold text-white text-base">Direct Stream Dilindungi Token</h4>
                <p className="text-xs text-[#94A3B8] max-w-sm">
                  Provider video ini memerlukan player resmi. Silakan beralih ke Player 1 (Embed).
                </p>
                <button
                  onClick={() => {
                    setHasNativeError(false);
                    setPlayerMode('embed');
                  }}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#8B5CF6] to-[#3B82F6] text-white font-bold text-xs shadow-lg"
                >
                  Beralih ke Player 1 (Embed)
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Video Details & Action Button Group (Watch Now, Open Source, Favorite, Share) */}
      <div className="bg-[#0D111B] border border-white/[0.08] rounded-3xl p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-md text-xs font-bold uppercase tracking-wider bg-[#8B5CF6]/90 text-white font-mono">
              {video.provider}
            </span>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-bold bg-[#141A27] border border-white/[0.08] text-[#94A3B8] font-mono">
              {video.quality || '4K UHD'}
            </span>
            <span className="text-xs text-[#94A3B8] font-mono">ID #{video.id}</span>
          </div>
          <span className="text-xs text-[#94A3B8]">Diunggah oleh @{video.username}</span>
        </div>

        <h1 className="text-xl sm:text-2xl font-black text-white leading-tight">
          {video.display_title || video.title}
        </h1>

        {/* VideoActionGroup Integration */}
        <VideoActionGroup
          video={video}
          onPlay={() => {
            if (playerMode === 'native') togglePlay();
          }}
          playLabel={isPlaying ? 'Jeda Video' : 'Putar Video'}
          onToggleFavorite={() => onToggleWatchlist?.(video)}
          isFavorite={isWatchlisted}
          size="md"
        />
      </div>
    </div>
  );
};
