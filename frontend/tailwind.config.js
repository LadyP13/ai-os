/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0f0f14',
        surface: '#1a1a24',
        accent: '#7c3aed',
        'accent-light': '#9d64f5',
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b',
        muted: '#64748b',
        'text-primary': '#e2e8f0',
        'text-secondary': '#94a3b8',
        border: '#2d2d3d',
      },
    },
  },
  plugins: [],
}
