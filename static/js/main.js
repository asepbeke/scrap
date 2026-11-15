/**
 * StreamVault - Global JavaScript Utilities (main.js)
 * Handles Watchlist, Toast notifications, Live Search, Video Detail Modal, and Navigation.
 */

// LocalStorage Keys
const WATCHLIST_KEY = "streamvault_watchlist";
const HISTORY_KEY = "streamvault_history";

// Global video memory store for clean event delegation
window.videoDataStore = window.videoDataStore || {};

// =========================================================================
// WATCHLIST STORAGE & BADGE MANAGEMENT
// =========================================================================
function getWatchlist() {
    try {
        return JSON.parse(localStorage.getItem(WATCHLIST_KEY)) || [];
    } catch (e) {
        return [];
    }
}

function saveWatchlist(items) {
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(items));
    updateWatchlistBadges();
}

function isWatchlisted(id) {
    const list = getWatchlist();
    return list.some(item => String(item.id) === String(id));
}

function toggleWatchlistItem(video) {
    if (!video || !video.id) return false;
    let list = getWatchlist();
    const idx = list.findIndex(item => String(item.id) === String(video.id));
    let added = false;

    if (idx >= 0) {
        list.splice(idx, 1);
        showToast("Dihapus dari Watchlist", "info");
        added = false;
    } else {
        list.unshift({
            id: video.id,
            display_title: video.display_title || video.title || "Untitled Video",
            thumbnail_url: video.thumbnail_url || video.thumbnail || "/static/placeholder.svg",
            provider: video.provider || "video",
            quality: video.quality || "4K UHD",
            duration: video.duration || "12:00",
            thread_key: video.thread_key || "live_show"
        });
        showToast("Ditambahkan ke Watchlist!", "success");
        added = true;
    }

    saveWatchlist(list);
    renderWatchlistDrawer();
    return added;
}

function updateWatchlistBadges() {
    const list = getWatchlist();
    const count = list.length;
    const b1 = document.getElementById("navWatchlistBadge");
    const b2 = document.getElementById("navWatchlistBadgeMobile");
    const b3 = document.getElementById("watchlistCountPill");

    if (b1) {
        b1.textContent = count;
        b1.classList.toggle("hidden", count === 0);
    }
    if (b2) {
        b2.textContent = count;
        b2.classList.toggle("hidden", count === 0);
    }
    if (b3) {
        b3.textContent = count;
    }
}

function toggleWatchlistModal() {
    const m = document.getElementById("watchlistModal");
    if (!m) return;
    if (m.classList.contains("hidden")) {
        m.classList.remove("hidden");
        m.classList.add("flex");
        renderWatchlistDrawer();
    } else {
        m.classList.add("hidden");
        m.classList.remove("flex");
    }
}

function renderWatchlistDrawer() {
    const container = document.getElementById("watchlistItemsList");
    if (!container) return;
    const items = getWatchlist();

    if (items.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 text-stream-muted space-y-2">
                <i class="fa-regular fa-heart text-3xl text-stream-border"></i>
                <p class="text-sm">Belum ada video yang disimpan.</p>
                <p class="text-xs">Klik tombol hati pada kartu video untuk menyimpannya di sini.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = items.map(v => `
        <div class="flex items-center gap-3 p-2.5 rounded-2xl bg-stream-card hover:bg-stream-cardHover border border-stream-borderLight transition group">
            <a href="/watch/${v.id}" class="w-20 h-14 rounded-xl overflow-hidden bg-black flex-shrink-0 relative">
                <img src="${v.thumbnail_url || '/static/placeholder.svg'}" alt="${v.display_title}" class="w-full h-full object-cover">
                <span class="absolute bottom-1 right-1 px-1 py-0.5 rounded text-[8px] font-mono bg-black/70 text-white font-bold">${v.duration || '12:00'}</span>
            </a>
            <div class="flex-1 min-w-0">
                <a href="/watch/${v.id}" class="text-xs font-bold text-white hover:text-stream-cyan transition line-clamp-1">
                    ${v.display_title}
                </a>
                <div class="flex items-center gap-1.5 mt-1 text-[10px] text-stream-muted">
                    <span class="text-stream-primary font-bold">${v.quality || '4K'}</span>
                    <span>•</span>
                    <span class="uppercase">${v.provider || 'video'}</span>
                </div>
            </div>
            <button type="button" onclick="removeWatchlistItem('${v.id}')" class="p-2 text-slate-400 hover:text-rose-400 transition" title="Hapus">
                <i class="fa-solid fa-trash-can text-xs"></i>
            </button>
        </div>
    `).join("");
}

function removeWatchlistItem(id) {
    let list = getWatchlist().filter(item => String(item.id) !== String(id));
    saveWatchlist(list);
    renderWatchlistDrawer();
    showToast("Video dihapus dari Watchlist", "info");
}

function clearWatchlist() {
    if (confirm("Kosongkan semua daftar Watchlist?")) {
        saveWatchlist([]);
        renderWatchlistDrawer();
        showToast("Watchlist dikosongkan", "info");
    }
}

// =========================================================================
// TOAST NOTIFICATION SYSTEM
// =========================================================================
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `pointer-events-auto px-4 py-3 rounded-2xl glass-panel border shadow-2xl flex items-center gap-3 text-xs font-semibold text-white transition-all transform duration-300 translate-y-4 opacity-0 ${
        type === 'success' ? 'border-emerald-500/40 text-emerald-300' : 
        type === 'error' ? 'border-rose-500/40 text-rose-300' : 'border-stream-primary/40 text-purple-200'
    }`;

    const icon = type === 'success' ? 'fa-circle-check text-emerald-400' : 
                 type === 'error' ? 'fa-circle-exclamation text-rose-400' : 'fa-bell text-stream-primary';

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove("translate-y-4", "opacity-0");
    }, 10);

    setTimeout(() => {
        toast.classList.add("opacity-0", "translate-y-2");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// =========================================================================
// LIVE SEARCH OVERLAY MODAL
// =========================================================================
let searchTimeout = null;

function openSearchModal() {
    const m = document.getElementById("searchModal");
    const inp = document.getElementById("globalSearchInput");
    if (m) {
        m.classList.remove("hidden");
        m.classList.add("flex");
        if (inp) inp.focus();
    }
}

function closeSearchModal() {
    const m = document.getElementById("searchModal");
    if (m) {
        m.classList.add("hidden");
        m.classList.remove("flex");
    }
}

function handleGlobalSearch(query) {
    clearTimeout(searchTimeout);
    const box = document.getElementById("searchResultsBox");
    if (!box) return;

    if (!query.trim()) {
        box.innerHTML = `
            <div class="text-center py-8 text-stream-muted text-sm">
                <i class="fa-solid fa-compass text-2xl text-stream-border mb-2 block"></i>
                Ketik kata kunci untuk mencari secara instan di ribuan video.
            </div>
        `;
        return;
    }

    searchTimeout = setTimeout(async () => {
        box.innerHTML = `<div class="text-center py-8 text-stream-muted text-xs"><i class="fa-solid fa-spinner fa-spin mr-2"></i> Mencari video...</div>`;
        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            if (!data.results || data.results.length === 0) {
                box.innerHTML = `
                    <div class="text-center py-8 text-stream-muted text-sm space-y-1">
                        <i class="fa-solid fa-film-slash text-2xl text-stream-border mb-2 block"></i>
                        <p>Tidak ditemukan video dengan kata kunci "<strong>${query}</strong>".</p>
                    </div>
                `;
                return;
            }

            box.innerHTML = data.results.map(v => `
                <a href="/watch/${v.id}" class="flex items-center gap-3 p-3 rounded-2xl bg-stream-card hover:bg-stream-cardHover border border-stream-borderLight transition group">
                    <div class="w-16 h-12 rounded-xl overflow-hidden bg-black flex-shrink-0 relative">
                        <img src="${v.thumbnail_url || '/static/placeholder.svg'}" alt="${v.display_title}" class="w-full h-full object-cover">
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-xs font-bold text-white group-hover:text-stream-cyan transition line-clamp-1">
                            ${v.display_title}
                        </div>
                        <div class="flex items-center gap-2 mt-1 text-[10px] text-stream-muted">
                            <span class="text-stream-primary font-bold">${v.quality || '4K'}</span>
                            <span>•</span>
                            <span>@${v.username || 'user'}</span>
                            <span>•</span>
                            <span class="uppercase">${v.provider || 'video'}</span>
                        </div>
                    </div>
                    <i class="fa-solid fa-play text-xs text-stream-muted group-hover:text-stream-cyan transition pr-2"></i>
                </a>
            `).join("");
        } catch (e) {
            box.innerHTML = `<div class="text-center py-6 text-rose-400 text-xs">Gagal melakukan pencarian: ${e.message}</div>`;
        }
    }, 250);
}

// =========================================================================
// SECURE URL OPENER (HTTP/HTTPS ONLY)
// =========================================================================
function openSecureNewTab(url, event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    if (!url || typeof url !== 'string' || !url.trim()) {
        showToast("URL sumber tidak tersedia", "error");
        return;
    }
    const cleanUrl = url.trim();
    try {
        const parsed = new URL(cleanUrl, window.location.href);
        if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
            showToast("Protokol URL tidak aman (hanya HTTP/HTTPS diperbolehkan)", "error");
            return;
        }
        window.open(parsed.href, '_blank', 'noopener,noreferrer');
    } catch (e) {
        showToast("Format URL tidak valid", "error");
    }
}

// =========================================================================
// DURATION FORMATTER & SYNCHRONIZATION
// =========================================================================
function formatDuration(val) {
    if (!val && val !== 0) return null;
    if (typeof val === 'number') {
        if (isNaN(val) || val <= 0) return "00:00";
        const h = Math.floor(val / 3600);
        const m = Math.floor((val % 3600) / 60);
        const s = Math.floor(val % 60);
        if (h > 0) {
            return `${h}:${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
        }
        return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
    }
    if (typeof val === 'string') {
        const str = val.trim();
        if (!str || str === '0' || str === '00:00') return null;
        if (/^\d+$/.test(str)) {
            return formatDuration(parseInt(str, 10));
        }
        if (/^\d{1,2}:\d{2}(:\d{2})?$/.test(str)) {
            return str;
        }
        return str;
    }
    return null;
}

function getSynchronizedDuration(video) {
    if (!video) return "14:20";

    // 1. Check cached duration probed from actual video stream
    try {
        const cached = localStorage.getItem("streamvault_dur_" + video.id);
        if (cached && cached !== "00:00") {
            return cached;
        }
    } catch(e) {}

    // 2. Check continue watching / history from real playback
    try {
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
        const hist = history.find(h => String(h.id) === String(video.id));
        if (hist && hist.duration && hist.duration !== "00:00") {
            return hist.duration;
        }
    } catch(e) {}

    // 3. Check video properties
    const parsed = formatDuration(video.duration) || formatDuration(video.duration_seconds);
    if (parsed && parsed !== "00:00") {
        return parsed;
    }

    return "14:20";
}

// =========================================================================
// GLOBAL VIDEO DETAIL QUICK-VIEW MODAL
// =========================================================================
let activeModalVideo = null;
let probeVideoElement = null;

function openVideoDetailModal(video) {
    if (!video) return;
    activeModalVideo = video;
    const m = document.getElementById("videoDetailModal");
    if (!m) return;

    const thumb = document.getElementById("modalThumbnail");
    if (thumb) thumb.src = video.thumbnail_url || video.thumbnail || '/static/placeholder.svg';

    const title = document.getElementById("modalTitle");
    if (title) title.textContent = video.display_title || video.title || "";

    const quality = document.getElementById("modalQuality");
    if (quality) quality.textContent = video.quality || "4K UHD";

    const provider = document.getElementById("modalProvider");
    if (provider) provider.textContent = (video.provider || "stream").toUpperCase();
    
    // Synchronize modalDuration directly with the video
    const durationEl = document.getElementById("modalDuration");
    const durationText = getSynchronizedDuration(video);
    if (durationEl) durationEl.textContent = durationText;

    const uploader = document.getElementById("modalUploader");
    if (uploader) uploader.textContent = `@${video.username || 'Unknown'}`;

    const page = document.getElementById("modalPage");
    if (page) page.textContent = `Forum Page #${video.forum_page || '1'}`;

    const idEl = document.getElementById("modalId");
    if (idEl) idEl.textContent = `ID #${video.id}`;

    const playBtn = document.getElementById("modalPlayBtn");
    if (playBtn) playBtn.href = `/watch/${video.id}`;

    const videoLink = video.video_url || video.videoUrl || video.direct_url || video.source_url || "";
    const openSourceBtn = document.getElementById("modalOpenSourceBtn");
    if (openSourceBtn) {
        if (videoLink) {
            openSourceBtn.disabled = false;
            openSourceBtn.classList.remove("opacity-40", "cursor-not-allowed");
            openSourceBtn.title = "Buka link video di tab baru: " + videoLink;
        } else {
            openSourceBtn.disabled = true;
            openSourceBtn.classList.add("opacity-40", "cursor-not-allowed");
            openSourceBtn.title = "Link video tidak tersedia";
        }
    }

    const favBtn = document.getElementById("modalFavBtn");
    if (favBtn) {
        const fav = isWatchlisted(video.id);
        favBtn.innerHTML = fav ? `<i class="fa-solid fa-heart text-rose-500"></i>` : `<i class="fa-regular fa-heart text-rose-500"></i>`;
    }

    // Live probe video stream metadata if available to ensure exact duration sync
    const streamUrl = video.video_url || video.videoUrl || video.direct_url;
    if (streamUrl && (streamUrl.includes(".mp4") || streamUrl.includes(".webm") || streamUrl.includes(".m3u8") || streamUrl.includes("dood") || streamUrl.includes("vidara"))) {
        try {
            if (!probeVideoElement) {
                probeVideoElement = document.createElement("video");
                probeVideoElement.preload = "metadata";
            }
            probeVideoElement.onloadedmetadata = () => {
                if (probeVideoElement.duration && isFinite(probeVideoElement.duration) && probeVideoElement.duration > 0) {
                    const exactDuration = formatDuration(probeVideoElement.duration);
                    if (exactDuration && activeModalVideo && String(activeModalVideo.id) === String(video.id)) {
                        if (durationEl) durationEl.textContent = exactDuration;
                        activeModalVideo.duration = exactDuration;
                        try {
                            localStorage.setItem("streamvault_dur_" + video.id, exactDuration);
                            document.querySelectorAll(`[data-video-id="${video.id}"]`).forEach(el => {
                                el.textContent = exactDuration;
                            });
                        } catch(e) {}
                    }
                }
            };
            probeVideoElement.src = streamUrl;
        } catch(e) {}
    }

    m.classList.remove("hidden");
    m.classList.add("flex");
}

function openVideoDetailModalById(id) {
    if (window.videoDataStore && window.videoDataStore[id]) {
        openVideoDetailModal(window.videoDataStore[id]);
        return;
    }
    // Fallback: Fetch from API
    fetch(`/api/video/${id}`)
        .then(res => res.json())
        .then(data => {
            if (data && data.video) {
                if (window.videoDataStore) window.videoDataStore[id] = data.video;
                openVideoDetailModal(data.video);
            } else {
                showToast("Video tidak ditemukan", "error");
            }
        })
        .catch(() => showToast("Gagal memuat informasi video", "error"));
}

function openModalSource(event) {
    if (!activeModalVideo) return;
    const url = activeModalVideo.video_url || activeModalVideo.videoUrl || activeModalVideo.direct_url || activeModalVideo.source_url;
    openSecureNewTab(url, event);
}

function closeVideoDetailModal() {
    const m = document.getElementById("videoDetailModal");
    if (m) {
        m.classList.add("hidden");
        m.classList.remove("flex");
    }
}

function toggleModalWatchlist() {
    if (!activeModalVideo) return;
    const fav = toggleWatchlistItem(activeModalVideo);
    const favBtn = document.getElementById("modalFavBtn");
    if (favBtn) {
        favBtn.innerHTML = fav ? `<i class="fa-solid fa-heart text-rose-500"></i>` : `<i class="fa-regular fa-heart text-rose-500"></i>`;
    }
}

function copyModalLink() {
    if (!activeModalVideo) return;
    const url = activeModalVideo.video_url || `${window.location.origin}/watch/${activeModalVideo.id}`;
    navigator.clipboard.writeText(url).then(() => {
        showToast("Link video berhasil disalin ke clipboard!", "success");
    });
}

function toggleMobileMenu() {
    const d = document.getElementById("mobileDrawer");
    if (d) d.classList.toggle("hidden");
}

// =========================================================================
// KEYBOARD SHORTCUTS & EVENT LISTENERS
// =========================================================================
document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        openSearchModal();
    } else if (e.key === "Escape") {
        closeSearchModal();
        closeVideoDetailModal();
        const wm = document.getElementById("watchlistModal");
        if (wm && !wm.classList.contains("hidden")) {
            wm.classList.add("hidden");
            wm.classList.remove("flex");
        }
    }
});

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    updateWatchlistBadges();
});
