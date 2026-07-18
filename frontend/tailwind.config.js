/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#101827",
        panel: "#1c2738",
        line: "#33445f",
        accent: "#66e3ba",
        text: "#e8eef9",
        muted: "#a9b8d0",
        warn: "#f7c66b",
        danger: "#ff8d99",
      }
    },
  },
  plugins: [],
}
