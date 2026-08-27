/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        felt: {
          DEFAULT: "#0b3d2e",
          dark: "#082c21",
          light: "#125239",
        },
        rail: "#1a1a1a",
        chip: {
          red: "#b3122c",
          redDark: "#7d0c1f",
        },
      },
      fontFamily: {
        display: ["Georgia", "serif"],
      },
    },
  },
  plugins: [],
};
