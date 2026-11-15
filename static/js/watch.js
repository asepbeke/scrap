/**
 * StreamVault - Watch Page JavaScript (watch.js)
 * Dual-Engine playback (Iframe embed + Native HLS/MP4), luxury cinema controls, adblock shields, and shortcuts.
 */

let playerMode = "embed"; // "embed", "direct", "native"
let isShieldStrict = true;
let hlsInstance = null;
let controlsHideTimeout = null;
let toolbarHideTimeout = null;

// =========================================================================
// PLAYER SWITCHING LOGIC (Embed / Direct / Native HLS)
// =========================================================================
function switchPlayerMode(mode) {
    playerMode = mode;
    const iframeBox = document.getElementById("iframePlayerContainer");
    const nativeBox = document.getElementById("nativePlayerContainer");
    const directBar = document.getElementById("directStreamBar");
    const iframe = document.getElementById("cinemaIframe");
    const nativeVideo = document.getElementById("nativeVideo");

    const btn1 = document.getElementById("btnPlayer1");
    const btn2 = document.getElementById("btnPlayer2");
    const btn3 = document.getElementById("btnPlayer3");

    [btn1, btn2, btn3].forEach(b => {
        if (b) {
            b.classList.remove("bg-gradient-to-r", "from-stream-primary", "to-stream-accent", "text-white", "shadow-glow-primary");
            b.classList.add("text-stream-muted");
        }
    });

    const embedUrl = window.watchConfig ? window.watchConfig.embedUrl : "";
    const directUrl = window.watchConfig ? window.watchConfig.directUrl : "";

    if (mode === "embed") {
        if (btn1) {
            btn1.classList.add("bg-gradient-to-r", "from-stream-primary", "to-stream-accent", "text-white", "shadow-glow-primary");
            btn1.classList.remove("text-stream-muted");
        }
        if (iframeBox) iframeBox.classList.remove("hidden");
        if (nativeBox) nativeBox.classList.add("hidden");
        if (directBar) directBar.classList.add("hidden");
        if (iframe) iframe.src = embedUrl;
        if (nativeVideo) nativeVideo.pause();
        showToast("Player 1 (Embed) Aktif", "info");
    } else if (mode === "direct") {
        if (btn2) {
            btn2.classList.add("bg-gradient-to-r", "from-stream-primary", "to-stream-accent", "text-white", "shadow-glow-primary");
            btn2.classList.remove("text-stream-muted");
        }
        if (iframeBox) iframeBox.classList.remove("hidden");
        if (nativeBox) nativeBox.classList.add("hidden");
        if (directBar) directBar.classList.add("hidden");
        if (iframe) iframe.src = directUrl;
        if (nativeVideo) nativeVideo.pause();
        showToast("Player 2 (Direct) Aktif", "info");
    } else if (mode === "native") {
        if (btn3) {
            btn3.classList.add("bg-gradient-to-r", "from-stream-primary", "to-stream-accent", "text-white", "shadow-glow-primary");
            btn3.classList.remove("text-stream-muted");
        }
        if (iframeBox) iframeBox.classList.add("hidden");
        if (nativeBox) nativeBox.classList.remove("hidden");
        if (directBar) directBar.classList.remove("hidden");
        initNativePlayback(directUrl);
        showToast("Player 3 (Native HLS/MP4) Aktif", "info");
    }
}

// =========================================================================
// NATIVE PLAYER ENGINE & HLS.JS
// =========================================================================
function initNativePlayback(url) {
    const video = document.getElementById("nativeVideo");
    const errBox = document.getElementById("nativeErrorState");
    if (!video) return;
    if (errBox) errBox.classList.add("hidden");

    if (hlsInstance) {
        hlsInstance.destroy();
        hlsInstance = null;
    }

    if (url && url.includes(".m3u8") && typeof Hls !== "undefined" && Hls.isSupported()) {
        hlsInstance = new Hls({
            enableWorker: true,
            lowLatencyMode: true
        });
        hlsInstance.loadSource(url);
        hlsInstance.attachMedia(video);
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, function () {
            video.play().catch(e => console.log("Autoplay blocked:", e));
        });
        hlsInstance.on(Hls.Events.ERROR, function (event, data) {
            if (data.fatal && errBox) {
                errBox.classList.remove("hidden");
            }
        });
    } else if (url) {
        // Normal MP4 / Direct Video Source
        video.src = url;
        video.load();
        video.play().catch(e => {
            console.log("Direct play notice:", e);
            if (!url.endsWith(".mp4") && !url.includes("blob:") && errBox) {
                errBox.classList.remove("hidden");
            }
        });
    }
}

function retryNativePlay() {
    const inp = document.getElementById("customStreamInput");
    const directUrl = window.watchConfig ? window.watchConfig.directUrl : "";
    const url = inp ? inp.value.trim() : directUrl;
    initNativePlayback(url);
}

function loadCustomStream() {
    const inp = document.getElementById("customStreamInput");
    if (inp && inp.value.trim()) {
        switchPlayerMode("native");
        initNativePlayback(inp.value.trim());
        showToast("Memuat stream custom...", "info");
    }
}

// =========================================================================
// LUXURY VIDEO CONTROLS LOGIC
// =========================================================================
function togglePlay() {
    const video = document.getElementById("nativeVideo");
    const playIcon = document.getElementById("controlPlayIcon");
    const bigPlayBtn = document.getElementById("bigCenterPlayBtn");
    const bigPlayIcon = document.getElementById("bigPlayIcon");
    if (!video) return;

    if (video.paused) {
        video.play();
        if (playIcon) playIcon.className = "fa-solid fa-pause text-sm";
        if (bigPlayIcon) bigPlayIcon.className = "fa-solid fa-pause text-2xl";
        if (bigPlayBtn) bigPlayBtn.classList.add("opacity-0", "pointer-events-none");
    } else {
        video.pause();
        if (playIcon) playIcon.className = "fa-solid fa-play text-sm";
        if (bigPlayIcon) bigPlayIcon.className = "fa-solid fa-play text-2xl pl-1";
        if (bigPlayBtn) bigPlayBtn.classList.remove("opacity-0", "pointer-events-none");
    }
}

function toggleMute() {
    const video = document.getElementById("nativeVideo");
    const icon = document.getElementById("controlVolumeIcon");
    const slider = document.getElementById("volumeSlider");
    if (!video) return;

    video.muted = !video.muted;
    if (video.muted) {
        if (icon) icon.className = "fa-solid fa-volume-xmark text-rose-400";
        if (slider) slider.value = 0;
    } else {
        if (icon) icon.className = "fa-solid fa-volume-high";
        if (slider) slider.value = video.volume || 1;
    }
}

function changeVolume(val) {
    const video = document.getElementById("nativeVideo");
    const icon = document.getElementById("controlVolumeIcon");
    if (!video) return;

    video.volume = val;
    video.muted = (val == 0);
    if (!icon) return;
    if (val == 0) {
        icon.className = "fa-solid fa-volume-xmark text-rose-400";
    } else if (val < 0.5) {
        icon.className = "fa-solid fa-volume-low";
    } else {
        icon.className = "fa-solid fa-volume-high";
    }
}

function setPlaybackSpeed(speed) {
    const video = document.getElementById("nativeVideo");
    if (video) video.playbackRate = speed;
    const disp = document.getElementById("speedDisplay");
    if (disp) disp.textContent = `${speed}x`;
    showToast(`Kecepatan putar diatur ke ${speed}x`, "info");
}

function togglePiP() {
    const video = document.getElementById("nativeVideo");
    if (document.pictureInPictureElement) {
        document.exitPictureInPicture();
    } else if (document.pictureInPictureEnabled && video) {
        video.requestPictureInPicture().catch(() => {
            showToast("Picture in Picture tidak didukung", "error");
        });
    }
}

function toggleFullscreen() {
    const player = document.getElementById("nativePlayerContainer");
    const icon = document.getElementById("fullscreenIcon");
    if (!player) return;

    if (!document.fullscreenElement) {
        player.requestFullscreen().then(() => {
            if (icon) icon.className = "fa-solid fa-compress text-sm";
        });
    } else {
        document.exitFullscreen().then(() => {
            if (icon) icon.className = "fa-solid fa-expand text-sm";
        });
    }
}

function toggleCinemaFullscreen() {
    const wrapper = document.getElementById("cinemaWrapper") || document.getElementById("nativePlayerContainer");
    const icon = document.getElementById("cinemaFullscreenIcon");
    if (!wrapper) return;

    if (!document.fullscreenElement) {
        if (wrapper.requestFullscreen) {
            wrapper.requestFullscreen().then(() => {
                if (icon) icon.className = "fa-solid fa-compress text-xs";
            });
        }
    } else {
        document.exitFullscreen().then(() => {
            if (icon) icon.className = "fa-solid fa-expand text-xs";
        });
    }
}

function formatTime(seconds) {
    if (isNaN(seconds)) return "00:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
}

// =========================================================================
// CONTINUE WATCHING STORAGE FOR WATCH PAGE
// =========================================================================
function saveContinueWatching(currentTime, duration, percent) {
    const currentVideo = window.currentWatchVideo;
    if (!currentVideo) return;
    let history = [];
    try {
        history = JSON.parse(localStorage.getItem("streamvault_history")) || [];
    } catch (e) {
        history = [];
    }

    const idx = history.findIndex(h => String(h.id) === String(currentVideo.id));
    const entry = {
        id: currentVideo.id,
        display_title: currentVideo.display_title,
        thumbnail_url: currentVideo.thumbnail_url,
        provider: currentVideo.provider,
        video_url: currentVideo.video_url || currentVideo.videoUrl || currentVideo.direct_url,
        videoUrl: currentVideo.video_url || currentVideo.videoUrl || currentVideo.direct_url,
        progressTime: formatTime(currentTime),
        duration: formatTime(duration),
        progressPercent: Math.round(percent),
        timestamp: Date.now()
    };

    if (idx >= 0) {
        history[idx] = entry;
    } else {
        history.unshift(entry);
    }

    history = history.slice(0, 20);
    localStorage.setItem("streamvault_history", JSON.stringify(history));
    try {
        if (duration && duration > 0) {
            localStorage.setItem("streamvault_dur_" + currentVideo.id, formatTime(duration));
        }
    } catch(e) {}
}

// =========================================================================
// ADBLOCK & SANDBOX SHIELDING
// =========================================================================
function toggleAdblockShield() {
    const iframe = document.getElementById("cinemaIframe");
    const text = document.getElementById("shieldModeText");
    if (!iframe || !text) return;

    isShieldStrict = !isShieldStrict;
    if (isShieldStrict) {
        iframe.setAttribute("sandbox", "allow-scripts allow-same-origin allow-presentation allow-forms");
        text.textContent = "Ketat";
        text.className = "text-emerald-400 font-bold";
        showToast("Mode Shield Ketat: Pop-up iklan diblokir", "success");
    } else {
        iframe.removeAttribute("sandbox");
        text.textContent = "Standar";
        text.className = "text-amber-400 font-bold";
        showToast("Mode Standar: Semua fitur iframe diizinkan", "info");
    }
    iframe.src = iframe.src;
}

function reloadPlayer() {
    const icon = document.getElementById("reloadIcon");
    if (icon) icon.classList.add("fa-spin");
    const iframe = document.getElementById("cinemaIframe");
    if (iframe) iframe.src = iframe.src;
    if (icon) setTimeout(() => icon.classList.remove("fa-spin"), 1000);
    showToast("Pemutar dimuat ulang", "info");
}

function toggleTheaterMode() {
    document.body.classList.toggle("theater-mode");
    const isTheater = document.body.classList.contains("theater-mode");
    showToast(isTheater ? "Mode Bioskop Aktif" : "Mode Normal", "info");
}

function copyWatchLink(url) {
    if (!url) return;
    navigator.clipboard.writeText(url).then(() => {
        showToast("Link video berhasil disalin!", "success");
    });
}

function toggleWatchPlayerWatchlist() {
    const currentVideo = window.currentWatchVideo;
    if (!currentVideo) return;
    const fav = toggleWatchlistItem(currentVideo);
    const icon = document.getElementById("watchFavIcon");
    if (icon) {
        icon.className = fav ? 
            "fa-solid fa-heart text-base text-rose-500 group-hover:scale-110 transition-transform" : 
            "fa-regular fa-heart text-base text-rose-500 group-hover:scale-110 transition-transform";
    }
}

function openShortcutsModal() {
    const m = document.getElementById("shortcutsModal");
    if (m) {
        m.classList.remove("hidden");
        m.classList.add("flex");
    }
}

function closeShortcutsModal() {
    const m = document.getElementById("shortcutsModal");
    if (m) {
        m.classList.add("hidden");
        m.classList.remove("flex");
    }
}

// =========================================================================
// EVENT LISTENERS & SHORTCUTS
// =========================================================================
document.addEventListener("keydown", (e) => {
    if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;

    const video = document.getElementById("nativeVideo");

    if (e.code === "Space" || e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (playerMode === "native") togglePlay();
    } else if (e.key.toLowerCase() === "f") {
        e.preventDefault();
        toggleFullscreen();
    } else if (e.key.toLowerCase() === "m") {
        e.preventDefault();
        toggleMute();
    } else if (e.key === "ArrowLeft" || e.key.toLowerCase() === "j") {
        e.preventDefault();
        if (video) video.currentTime = Math.max(0, video.currentTime - 5);
    } else if (e.key === "ArrowRight" || e.key.toLowerCase() === "l") {
        e.preventDefault();
        if (video) video.currentTime = Math.min(video.duration || 0, video.currentTime + 5);
    } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (video) changeVolume(Math.min(1, (video.volume || 1) + 0.1));
    } else if (e.key === "ArrowDown") {
        e.preventDefault();
        if (video) changeVolume(Math.max(0, (video.volume || 1) - 0.1));
    } else if (e.key.toLowerCase() === "p") {
        e.preventDefault();
        togglePiP();
    } else if (e.key === "?") {
        openShortcutsModal();
    }
});

// Auto-hide floating action toolbar & controls overlay on mouse inactivity
document.addEventListener("DOMContentLoaded", () => {
    const cinemaWrapper = document.getElementById("cinemaWrapper");
    if (cinemaWrapper) {
        cinemaWrapper.addEventListener("mousemove", () => {
            const toolbar = document.getElementById("floatingPlayerToolbar");
            if (toolbar) {
                toolbar.classList.remove("opacity-0", "pointer-events-none");
                toolbar.classList.add("opacity-90");
                clearTimeout(toolbarHideTimeout);
                toolbarHideTimeout = setTimeout(() => {
                    if (!toolbar.matches(":hover")) {
                        toolbar.classList.remove("opacity-90");
                        toolbar.classList.add("opacity-0", "pointer-events-none");
                    }
                }, 2500);
            }
        });
        cinemaWrapper.addEventListener("mouseleave", () => {
            const toolbar = document.getElementById("floatingPlayerToolbar");
            if (toolbar) {
                clearTimeout(toolbarHideTimeout);
                toolbar.classList.remove("opacity-90");
                toolbar.classList.add("opacity-0", "pointer-events-none");
            }
        });
    }

    const nativeContainer = document.getElementById("nativePlayerContainer");
    if (nativeContainer) {
        nativeContainer.addEventListener("mousemove", () => {
            const overlay = document.getElementById("customControlsOverlay");
            if (overlay) {
                overlay.classList.remove("opacity-0");
                clearTimeout(controlsHideTimeout);
                const video = document.getElementById("nativeVideo");
                if (video && !video.paused) {
                    controlsHideTimeout = setTimeout(() => {
                        overlay.classList.add("opacity-0");
                    }, 2500);
                }
            }
        });
    }

    // Time update & Scrubbing for Native Video
    const nativeVideo = document.getElementById("nativeVideo");
    if (nativeVideo) {
        nativeVideo.addEventListener("timeupdate", () => {
            const cur = nativeVideo.currentTime;
            const dur = nativeVideo.duration || 1;
            const percent = (cur / dur) * 100;

            const progressBar = document.getElementById("playProgressBar");
            if (progressBar) progressBar.style.width = `${percent}%`;

            const curDisp = document.getElementById("currentTimeDisplay");
            if (curDisp) curDisp.textContent = formatTime(cur);

            const durDisp = document.getElementById("durationTimeDisplay");
            if (durDisp) durDisp.textContent = formatTime(dur);

            saveContinueWatching(cur, dur, percent);
        });

        nativeVideo.addEventListener("loadedmetadata", () => {
            const dur = nativeVideo.duration;
            if (dur && isFinite(dur) && dur > 0) {
                const durStr = formatTime(dur);
                const durDisp = document.getElementById("durationTimeDisplay");
                if (durDisp) durDisp.textContent = durStr;
                try {
                    if (window.currentWatchVideo) {
                        localStorage.setItem("streamvault_dur_" + window.currentWatchVideo.id, durStr);
                    }
                } catch(e) {}
            }
        });

        nativeVideo.addEventListener("progress", () => {
            if (nativeVideo.buffered.length > 0) {
                const bufferedEnd = nativeVideo.buffered.end(nativeVideo.buffered.length - 1);
                const dur = nativeVideo.duration || 1;
                const bufBar = document.getElementById("bufferedProgressBar");
                if (bufBar) bufBar.style.width = `${(bufferedEnd / dur) * 100}%`;
            }
        });
    }

    // Scrub bar click handler
    const progressContainer = document.getElementById("progressContainer");
    if (progressContainer) {
        progressContainer.addEventListener("click", (e) => {
            const rect = progressContainer.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            const video = document.getElementById("nativeVideo");
            if (video) video.currentTime = pos * (video.duration || 0);
        });
    }

    // Initial favorite icon state
    const currentVideo = window.currentWatchVideo;
    const icon = document.getElementById("watchFavIcon");
    if (icon && currentVideo && isWatchlisted(currentVideo.id)) {
        icon.className = "fa-solid fa-heart text-base text-rose-500 group-hover:scale-110 transition-transform";
    }

    // Record initial view in history
    if (currentVideo) {
        saveContinueWatching(1, currentVideo.duration_seconds || 600, 1);
    }
});
