import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: "#080808",
          900: "#0f0f0f",
          800: "#1a1a1a",
          700: "#242424",
          600: "#2e2e2e",
          500: "#3a3a3a",
          400: "#4a4a4a",
        },
        importance: {
          critical: "#dc2626",
          executive: "#f59e0b",
          technical: "#3b82f6",
          research: "#a855f7",
          approved: "#22c55e",
          archived: "#6b7280",
        },
        glass: {
          border: "rgba(255, 255, 255, 0.08)",
          surface: "rgba(255, 255, 255, 0.04)",
          hover: "rgba(255, 255, 255, 0.07)",
          active: "rgba(255, 255, 255, 0.1)",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "system-ui",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      backdropBlur: {
        glass: "12px",
      },
      boxShadow: {
        glass: "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)",
        card: "0 2px 8px rgba(0,0,0,0.3)",
        "card-hover": "0 4px 16px rgba(0,0,0,0.5)",
      },
      animation: {
        "fade-in": "fadeIn 0.15s ease-out",
        "slide-up": "slideUp 0.2s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
