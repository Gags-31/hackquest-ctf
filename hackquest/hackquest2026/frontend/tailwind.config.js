/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        void: '#05070d',
        panel: '#0b1020',
        neon: '#39ff14',
        cyan: '#22d3ee',
        violet: '#a855f7',
      },
      fontFamily: {
        display: ['Space Grotesk', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 24px rgba(57,255,20,0.18)',
        cyan: '0 0 24px rgba(34,211,238,0.18)',
      },
      keyframes: {
        marquee: { '0%': { transform: 'translateX(0)' }, '100%': { transform: 'translateX(-50%)' } },
        float: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' } },
        pulseGlow: { '0%,100%': { opacity: '0.55' }, '50%': { opacity: '1' } },
        scan: { '0%': { transform: 'translateY(-100%)' }, '100%': { transform: 'translateY(100%)' } },
      },
      animation: {
        marquee: 'marquee 28s linear infinite',
        float: 'float 6s ease-in-out infinite',
        pulseGlow: 'pulseGlow 2.5s ease-in-out infinite',
        scan: 'scan 6s linear infinite',
      },
    },
  },
  plugins: [],
}
