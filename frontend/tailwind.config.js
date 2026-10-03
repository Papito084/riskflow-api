/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#090a0f',
          surface: '#11131a',
          card: '#161923',
          border: '#232736',
          muted: '#8e96a8',
        },
        profit: {
          DEFAULT: '#10b981',
          light: '#34d399',
          glow: 'rgba(16, 185, 129, 0.15)',
        },
        loss: {
          DEFAULT: '#f43f5e',
          light: '#fb7185',
          glow: 'rgba(244, 63, 94, 0.15)',
        },
      },
    },
  },
  plugins: [],
}
