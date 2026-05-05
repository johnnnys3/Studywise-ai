import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        study: {
          navy: "#0F172A",
          slate: "#475569",
          accent: "#0EA5E9",
          surface: "#F7F9FB",
          line: "#E2E8F0",
        },
      },
      boxShadow: {
        academic: "0 4px 20px rgba(15, 23, 42, 0.1)",
      },
      fontFamily: {
        ui: ["Inter", "system-ui", "sans-serif"],
        reading: ["Newsreader", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
