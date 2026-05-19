/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1A1A1A",
        "ink-2": "#333333",
        paper: "#FFFFFF",
        "paper-2": "#FAFAFA",
        "paper-3": "#F4F4F4",
        line: "#E5E5E5",
        "line-dark": "#D0D0D0",
        mute: "#8A8A8A",
        "mute-2": "#666666",
        accent: "#C8102E",
        "accent-dark": "#9E0B23",
        "accent-soft": "#FCE9EC",
        "rag-green": "#2F7D4F",
        "rag-amber": "#B8740A",
        "rag-red": "#C8102E",
        "rag-green-bg": "#EDF5EF",
        "rag-amber-bg": "#FAF1E0",
        "rag-red-bg": "#FBE8EB",
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        body: ['"Geist"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
