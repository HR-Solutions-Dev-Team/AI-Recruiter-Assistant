/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#C026D3',
          50: '#FAE8FF',
          100: '#F5D0FE',
          200: '#F0ABFC',
          300: '#E879F9',
          400: '#D946EF',
          500: '#C026D3',
          600: '#A21CAF',
          700: '#86198F',
          800: '#701A75',
          900: '#581C87',
        },
      },
      transitionDuration: {
        '300': '300ms',
      },
    },
  },
  plugins: [],
}
