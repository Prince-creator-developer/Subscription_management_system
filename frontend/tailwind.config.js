/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        odoo: {
          primary: '#714B67',    // Classic Odoo Deep Purple
          hover: '#5D3D54',
          secondary: '#008784',  // Odoo Teal Accent
          accent: '#00A09D',
          dark: '#1E293B',
          light: '#F8FAFC',
          card: '#FFFFFF',
          border: '#E2E8F0',
        }
      }
    },
  },
  plugins: [],
}
