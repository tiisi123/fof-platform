/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f7ff', 100: '#e0efff', 200: '#b8dcff', 300: '#7ac0ff',
          400: '#349eff', 500: '#0a7df5', 600: '#0060d4', 700: '#004aab',
          800: '#00408f', 900: '#063776',
        },
        accent: { gold: '#d4af37', success: '#10b981', warning: '#f59e0b', danger: '#ef4444' },
        dark: {
          50: '#f8fafc', 100: '#f1f5f9', 200: '#e2e8f0', 300: '#cbd5e1',
          400: '#94a3b8', 500: '#64748b', 600: '#475569', 700: '#334155',
          800: '#1e293b', 900: '#0f172a', 950: '#020617',
        }
      },
      boxShadow: {
        'glow': '0 0 20px rgba(10, 125, 245, 0.15)',
        'glow-lg': '0 0 40px rgba(10, 125, 245, 0.15)',
      },
    },
  },
  plugins: [],
}
