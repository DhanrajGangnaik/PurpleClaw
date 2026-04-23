/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: '#0f172a',
          panel: '#1f2937',
          panelAlt: '#111827',
          border: '#374151',
          indigo: '#4f46e5',
          indigoSoft: '#312e81',
          text: '#f3f4f6',
          muted: '#9ca3af',
          faint: '#6b7280',
        },
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '0.875rem',
      },
      boxShadow: {
        panel: '0 8px 24px rgba(15, 23, 42, 0.14)',
      },
    },
  },
  plugins: [],
};
