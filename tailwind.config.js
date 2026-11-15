/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './src/**/*.{js,ts,jsx,tsx}',
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './app/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        stream: {
          bg: '#080A0F',
          secondary: '#0D111B',
          surface: '#141A27',
          elevated: '#1B2232',
          card: '#141A27',
          cardHover: '#1B2232',
          border: 'rgba(255, 255, 255, 0.08)',
          borderLight: 'rgba(255, 255, 255, 0.08)',
          borderHover: 'rgba(255, 255, 255, 0.16)',
          primary: '#8B5CF6',
          primaryHover: '#7C3AED',
          accent: '#3B82F6',
          accentHover: '#2563EB',
          // Legacy mappings for backwards compatibility
          cyan: '#3B82F6',
          cyanHover: '#2563EB',
          text: '#F8FAFC',
          textSecondary: '#94A3B8',
          muted: '#64748B',
        },
      },
      boxShadow: {
        'glow-primary': '0 4px 24px -2px rgba(139, 92, 246, 0.35)',
        'glow-accent': '0 4px 24px -2px rgba(59, 130, 246, 0.3)',
        'glow-cyan': '0 4px 24px -2px rgba(59, 130, 246, 0.3)',
        'card-hover': '0 20px 40px -15px rgba(0, 0, 0, 0.7), 0 0 25px -5px rgba(139, 92, 246, 0.18)',
        'cinema': '0 25px 60px -15px rgba(0, 0, 0, 0.95)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        heading: ['Outfit', 'Plus Jakarta Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
