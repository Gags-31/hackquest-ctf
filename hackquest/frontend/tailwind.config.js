/** Tailwind configuration - dark navy with neon cyan and violet accents. */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#04070d",
          900: "#070b14",
          850: "#0a1020",
          800: "#0e1526",
          700: "#16203a",
          600: "#1e2c4d",
          500: "#2a3b63",
        },
        neon: {
          cyan: "#22d3ee",
          violet: "#a78bfa",
          lime: "#4ade80",
          amber: "#fbbf24",
          rose: "#fb7185",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(34,211,238,.35)",
        "glow-violet": "0 0 24px rgba(167,139,250,.35)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(.4,0,.6,1) infinite",
        drift: "drift 18s ease-in-out infinite alternate",
      },
      keyframes: {
        drift: {
          "0%": { transform: "translate3d(0,0,0)" },
          "100%": { transform: "translate3d(0,-18px,0)" },
        },
      },
    },
  },
  plugins: [],
};