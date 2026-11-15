/**
 * StreamVault - Index Page JavaScript (index.js)
 * Hero carousel controls, layout switching, continue watching row, and duration synchronization.
 */

// Global Hero State
let currentHeroIndex = 0;

// Horizontal row scrolling helper
function scrollRow(rowId, direction) {
    const row = document.getElementById(rowId);
    if (!row) return;
    const scrollAmount = row.clientWidth * 0.75;
    row.scrollBy({ left: direction * scrollAmount, behavior: 'smooth' });
}

// =========================================================================
// HERO SECTION SLIDE SWITCHER
// =========================================================================
function getHeroList() {
    return window.featuredVideosData || [];
}

function getCurrentHeroVideo() {
    const list = getHeroList();
    if (list.length > 0 && currentHeroIndex < list.length) {
        return list[currentHeroIndex];
    }
    return list[0] || null;
}

function openHeroDetailModal() {
    const vid = getCurrentHeroVideo();
    if (vid) {
        openVideoDetailModal(vid);
    }
}

function shareCurrentHeroVideo() {
    const vid = getCurrentHeroVideo();
    if (!vid) return;
    const sUrl = vid.video_url || vid.videoUrl || vid.direct_url || (window.location.origin + "/watch/" + vid.id);
    if (navigator.clipboard) {
        navigator.clipboard.writeText(sUrl).then(() => {
            showToast("Link video berhasil disalin!", "success");
        });
    }
}

function switchHeroSlideByIndex(index) {
    const list = getHeroList();
    if (!list || list.length <= index) return;
    currentHeroIndex = index;
    const video = list[index];

    const bImg = document.getElementById("heroBackdropImg");
    if (bImg) bImg.src = video.thumbnail_url || '/static/placeholder.svg';

    const titleEl = document.getElementById("heroTitle");
    if (titleEl) titleEl.textContent = video.display_title;

    const qualityEl = document.getElementById("heroQuality");
    if (qualityEl) qualityEl.textContent = video.quality || "4K UHD";

    const provEl = document.getElementById("heroProvider");
    if (provEl) provEl.textContent = (video.provider || "video").toUpperCase();

    // Synchronized duration for hero
    const dur = typeof getSynchronizedDuration === 'function' ? getSynchronizedDuration(video) : (video.duration || '18:45');
    const durEl = document.getElementById("heroDuration");
    if (durEl) durEl.innerHTML = `<i class="fa-regular fa-clock mr-1 text-[#8B5CF6]"></i> ${dur}`;

    const pageBadge = document.getElementById("heroPageBadge");
    if (pageBadge && video.forum_page) {
        pageBadge.innerHTML = `<i class="fa-solid fa-file-lines text-stream-primary mr-1"></i>Page ${video.forum_page}`;
    }

    const descEl = document.getElementById("heroDesc");
    if (descEl) {
        descEl.innerHTML = `Video rilis terbaru dari <strong>Page ${video.forum_page || 'Terbaru'}</strong> diunggah oleh <strong>@${video.username || 'Unknown'}</strong> di saluran ${video.thread_name || 'StreamVault'}. Nikmati playback beresolusi tinggi dengan audio jernih dan kontrol pemutar bioskop modern.`;
    }

    const playBtn = document.getElementById("heroPlayBtn");
    if (playBtn) playBtn.href = `/watch/${video.id}`;
    
    // Update hero right preview poster card
    const posterImg = document.getElementById("heroPosterImg");
    if (posterImg) posterImg.src = video.thumbnail_url || '/static/placeholder.svg';

    const posterTitle = document.getElementById("heroPosterTitle");
    if (posterTitle) posterTitle.textContent = video.display_title;

    const posterDur = document.getElementById("heroPosterDuration");
    if (posterDur) posterDur.textContent = dur;

    const posterPage = document.getElementById("heroPosterPage");
    if (posterPage && video.forum_page) {
        posterPage.textContent = `Page ${video.forum_page} • Rilis Terbaru`;
    }

    // Update hero Open in New Tab button
    const openBtn = document.getElementById("heroOpenSourceBtn");
    if (openBtn) {
        const sUrl = video.video_url || video.videoUrl || video.direct_url || video.source_url || "";
        openBtn.onclick = (e) => openSecureNewTab(sUrl, e);
    }

    // Update carousel indicators
    document.querySelectorAll(".hero-indicator").forEach((dot, idx) => {
        if (idx === index) {
            dot.className = "hero-indicator h-1.5 rounded-full transition-all duration-300 w-8 bg-stream-primary";
        } else {
            dot.className = "hero-indicator h-1.5 rounded-full transition-all duration-300 w-3 bg-white/20 hover:bg-white/40";
        }
    });

    // Update hero favorite button
    const favBtn = document.getElementById("heroFavBtn");
    if (favBtn) {
        const fav = isWatchlisted(video.id);
        favBtn.innerHTML = fav ? `<i class="fa-solid fa-heart text-rose-500"></i>` : `<i class="fa-regular fa-heart"></i>`;
    }
}

function toggleHeroWatchlist() {
    const vid = getCurrentHeroVideo();
    if (!vid) return;
    const fav = toggleWatchlistItem(vid);
    const favBtn = document.getElementById("heroFavBtn");
    if (favBtn) {
        favBtn.innerHTML = fav ? `<i class="fa-solid fa-heart text-rose-500"></i>` : `<i class="fa-regular fa-heart"></i>`;
    }
}

function toggleCardWatchlistById(id, btn) {
    let video = null;
    if (window.videoDataStore && window.videoDataStore[id]) {
        video = window.videoDataStore[id];
    } else {
        video = { id: id };
    }
    const fav = toggleWatchlistItem(video);
    if (btn) {
        btn.innerHTML = fav ? `<i class="fa-solid fa-heart text-[11px] text-rose-500"></i>` : `<i class="fa-regular fa-heart text-[11px] text-rose-400"></i>`;
    }
}

// Backward compatibility helper
function toggleCardWatchlist(video, btn) {
    if (video && video.id) {
        if (window.videoDataStore) window.videoDataStore[video.id] = video;
        toggleCardWatchlistById(video.id, btn);
    }
}

// =========================================================================
// LAYOUT SWITCHER (Wide 16:9, Tall Poster, Fit)
// =========================================================================
function setLayout(mode) {
    localStorage.setItem("streamvault_layout", mode);
    const boxes = document.querySelectorAll(".thumb-box-container");
    const btnWide = document.getElementById("btnLayoutWide");
    const btnTall = document.getElementById("btnLayoutTall");
    const btnFit = document.getElementById("btnLayoutFit");

    boxes.forEach(b => {
        b.classList.remove("thumb-box-wide", "thumb-box-tall", "thumb-box-fit");
        if (mode === "tall") {
            b.classList.add("thumb-box-tall");
        } else if (mode === "fit") {
            b.classList.add("thumb-box-fit");
        } else {
            b.classList.add("thumb-box-wide");
        }
    });

    // Toggle active button styles
    [btnWide, btnTall, btnFit].forEach(btn => {
        if (btn) {
            btn.classList.remove("bg-gradient-to-r", "from-stream-primary", "to-stream-accent", "text-white");
            btn.classList.add("text-stream-muted");
        }
    });

    if (mode === "tall" && btnTall) {
        btnTall.classList.add("bg-gradient-to-r", "from-stream-primary", "to-stream-accent", "text-white");
        btnTall.classList.remove("text-stream-muted");
    } else if (mode === "fit" && btnFit) {
        btnFit.classList.add("bg-gradient-to-r", "from-stream-primary", "to-stream-accent", "text-white");
        btnFit.classList.remove("text-stream-muted");
    } else if (btnWide) {
        btnWide.classList.add("bg-gradient-to-r", "from-stream-primary", "to-stream-accent", "text-white");
        btnWide.classList.remove("text-stream-muted");
    }
}

// =========================================================================
// CONTINUE WATCHING (LOCALSTORAGE HYDRATION)
// =========================================================================
function loadContinueWatching() {
    const sec = document.getElementById("continueWatchingSection");
    const row = document.getElementById("continueRow");
    if (!sec || !row) return;

    let history = [];
    try {
        history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    } catch (e) {
        history = [];
    }

    if (history.length === 0) {
        sec.classList.add("hidden");
        return;
    }

    sec.classList.remove("hidden");
    row.innerHTML = history.map(item => `
        <div class="flex-shrink-0 w-64 sm:w-72 rounded-2xl overflow-hidden glass-card group hover:border-stream-primary/50 hover:shadow-card-hover transition-all duration-300">
            <div class="relative thumb-box-wide">
                <img src="${item.thumbnail_url || '/static/placeholder.svg'}" alt="${item.display_title}" class="w-full h-full object-cover">
                <!-- Progress Bar Overlay -->
                <div class="absolute bottom-0 left-0 right-0 h-1.5 bg-black/80">
                    <div class="h-full bg-gradient-to-r from-stream-primary to-stream-accent" style="width: ${item.progressPercent || 35}%;"></div>
                </div>
                <div class="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2 z-20 p-2">
                    <a href="/watch/${item.id}" class="w-10 h-10 rounded-full btn-action-play text-white flex items-center justify-center shadow-glow-primary hover:scale-110 transition-transform" title="Lanjutkan Menonton">
                        <i class="fa-solid fa-play text-xs pl-0.5"></i>
                    </a>
                    <button type="button" onclick="openSecureNewTab('${item.video_url || item.videoUrl || item.direct_url || item.source_url || ''}', event);" 
                            class="px-3 py-1 rounded-xl btn-action-glass text-slate-200 hover:text-white text-[10px] font-bold shadow-md transition-all flex items-center gap-1.5 group/src" 
                            title="Buka link video di tab baru (Open in New Tab)">
                        <i class="fa-solid fa-arrow-up-right-from-square text-[9px] text-slate-300 group-hover/src:text-white"></i>
                        <span>Open Source</span>
                    </button>
                </div>
            </div>
            <div class="p-3 space-y-1">
                <h4 class="text-xs font-bold text-[#F8FAFC] group-hover:text-purple-300 transition line-clamp-1">${item.display_title}</h4>
                <div class="flex items-center justify-between text-[10px] text-stream-muted">
                    <span class="text-stream-accent font-mono font-bold">${item.progressTime || '04:20'} / ${item.duration || '15:00'}</span>
                    <div class="flex items-center gap-1.5">
                        <button type="button" onclick="openSecureNewTab('${item.video_url || item.videoUrl || item.direct_url || item.source_url || ''}', event);" class="p-1 text-slate-300 hover:text-white transition" title="Buka link video di tab baru">
                            <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
                        </button>
                        <button type="button" onclick="removeHistoryItem('${item.id}')" class="p-1 text-slate-400 hover:text-rose-400 transition" title="Hapus dari riwayat">
                            <i class="fa-solid fa-xmark"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join("");
}

function removeHistoryItem(id) {
    let history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    history = history.filter(h => String(h.id) !== String(id));
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    loadContinueWatching();
}

// Sync all card duration pills from cache & watch history
function syncCardDurations() {
    try {
        // Check direct cached video durations
        document.querySelectorAll(".card-duration-pill").forEach(el => {
            const vId = el.getAttribute("data-video-id");
            if (vId) {
                const cached = localStorage.getItem("streamvault_dur_" + vId);
                if (cached && cached !== "00:00") {
                    el.textContent = cached;
                }
            }
        });

        // Check history for played durations
        const history = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
        history.forEach(item => {
            if (item.id && item.duration && item.duration !== "00:00") {
                document.querySelectorAll(`.card-duration-pill[data-video-id="${item.id}"]`).forEach(el => {
                    el.textContent = item.duration;
                });
            }
        });
    } catch(e) {}
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    const savedLayout = localStorage.getItem("streamvault_layout") || "wide";
    setLayout(savedLayout);
    loadContinueWatching();
    syncCardDurations();
});
