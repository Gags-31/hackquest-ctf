/** Tailwind config for the live-preview CSS build (scans the shared templates). */
export default {
  content: ["../frontend/src/**/*.{ts,tsx}", "./**/*.tsx"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef2ff", 100: "#e0e7ff", 500: "#6366f1", 600: "#4f46e5",
          700: "#4338ca", 900: "#312e81",
        },
      },
    },
  },
  plugins: [],
};
