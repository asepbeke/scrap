import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-20 border-t border-white/5 bg-[#11151D]/50 text-xs text-[#9CA3AF]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3">
            <span className="font-black text-lg text-white">
              Stream<span className="text-[#8B5CF6]">Vault</span>
            </span>
            <p className="leading-relaxed text-[11px]">
              Platform streaming modern kelas dunia dengan visual sinematik, pemutar canggih HLS & MP4, dan integrasi scraper realtime.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-bold text-white uppercase tracking-wider text-[11px]">Navigasi</h4>
            <ul className="space-y-1.5 text-[11px]">
              <li><a href="/" className="hover:text-white transition">Beranda</a></li>
              <li><a href="/?sort=popular" className="hover:text-white transition">Paling Populer</a></li>
              <li><a href="/?sort=newest" className="hover:text-white transition">Baru Ditambahkan</a></li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="font-bold text-white uppercase tracking-wider text-[11px]">Fitur Platform</h4>
            <ul className="space-y-1.5 text-[11px]">
              <li>✓ Dual Engine HLS & MP4 Player</li>
              <li>✓ AdBlock & Anti-Redirect Shield</li>
              <li>✓ Realtime Playwright CDP Live Scraping</li>
              <li>✓ Local Storage Continue Watching</li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="font-bold text-white uppercase tracking-wider text-[11px]">Legal & Kontak</h4>
            <ul className="space-y-1.5 text-[11px]">
              <li><span className="hover:text-white cursor-pointer transition">Kebijakan Privasi</span></li>
              <li><span className="hover:text-white cursor-pointer transition">Syarat & Ketentuan</span></li>
              <li><span className="hover:text-white cursor-pointer transition">Kontak Dukungan</span></li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px]">
          <p>&copy; 2026 StreamVault Studio. All rights reserved.</p>
          <div className="flex items-center gap-4 text-emerald-400 font-mono">
            ● System Operational
          </div>
        </div>
      </div>
    </footer>
  );
};

