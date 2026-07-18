import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F1F3EF",
        ink: "#1B2621",
        pine: "#2F4F3E",
        pineDeep: "#1F3A2C",
        clay: "#C77B5E",
        rule: "#CBD3C9",
        muted: "#5B665E",
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "serif"],
        body: ["var(--font-plex)", "sans-serif"],
        mono: ["var(--font-plex-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
