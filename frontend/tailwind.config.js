/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        github: {
          dark: "#0d1117",
          surface: "#161b22",
          border: "#30363d",
          accent: "#238636",
          blue: "#1f6feb",
          yellow: "#d29922",
          red: "#da3633",
          text: "#c9d1d9",
          muted: "#8b949e",
        },
      },
    },
  },
  plugins: [],
};
