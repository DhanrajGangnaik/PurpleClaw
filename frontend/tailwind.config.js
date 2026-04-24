/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // System colors
        corp: '#008FEC',
        xppurple: '#9013FE',
        danger: '#FC4D64',
        success: '#3EBD41',
        warning: '#F3AD38',

        // Dark layers
        'dark-basement': '#10131A',
        'dark-bg': '#141820',
        'dark-first': '#1A212D',
        'dark-second': '#1D2736',
        'dark-third': '#212D3F',

        // Light layers
        'light-basement': '#B6BBCC',
        'light-bg': '#E6E8EF',
        'light-first': '#F6F7F8',
        'light-second': '#FBFBFB',
        'light-third': '#FFFFFF',

        // Additional
        'light-yellow': '#F0DF47',
        'dark-orange': '#E88021',
        redish: '#D03F3F',
        pink: '#CD317C',
        violet: '#6227E0',
        'dark-blue': '#2264E3',
        'light-blue': '#27B4E0',
        aquamarine: '#27E087',
        'dark-green': '#139520',
        gray: '#646464',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Manrope', 'Avenir Next', 'Segoe UI', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '1rem',
        xl2: '1.25rem',
      },
      boxShadow: {
        card: '0 4px 24px rgba(8, 12, 24, 0.28)',
        panel: '0 8px 32px rgba(8, 12, 24, 0.32)',
        soft: '0 10px 24px rgba(8, 12, 24, 0.18)',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(90deg, #9013FE 0%, #008FEC 100%)',
        'brand-gradient-vertical': 'linear-gradient(180deg, #9013FE 0%, #008FEC 100%)',
      },
    },
  },
  plugins: [],
};
