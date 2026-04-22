/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        night: '#0f172a',
        panel: '#1e293b',
        cyanline: '#22d3ee',
        violetline: '#a855f7',
        signal: '#34d399',
      },
      boxShadow: {
        glow: '0 0 35px rgba(34, 211, 238, 0.14)',
        violet: '0 0 35px rgba(168, 85, 247, 0.14)',
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
