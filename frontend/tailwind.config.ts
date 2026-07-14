import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: "#0d1117",
          panel: "#12181f",
          elevated: "#161b22",
          border: "#30363d",
          muted: "#8b949e",
          text: "#e6edf3",
          yellow: "#ecad0a",
          blue: "#209dd7",
          purple: "#753991",
          green: "#3fb950",
          red: "#f85149",
          up: "rgba(63, 185, 80, 0.22)",
          down: "rgba(248, 81, 73, 0.22)",
        },
      },
      fontFamily: {
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "Liberation Mono",
          "monospace",
        ],
        sans: [
          "Inter",
          "Segoe UI",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
      boxShadow: {
        panel: "0 0 0 1px rgba(48, 54, 61, 0.8), 0 8px 24px rgba(0,0,0,0.35)",
      },
      keyframes: {
        flashUp: {
          "0%": { backgroundColor: "rgba(63, 185, 80, 0.35)" },
          "100%": { backgroundColor: "transparent" },
        },
        flashDown: {
          "0%": { backgroundColor: "rgba(248, 81, 73, 0.35)" },
          "100%": { backgroundColor: "transparent" },
        },
        pulseDot: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.45" },
        },
      },
      animation: {
        "flash-up": "flashUp 500ms ease-out",
        "flash-down": "flashDown 500ms ease-out",
        "pulse-dot": "pulseDot 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
