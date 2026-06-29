/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Cormorant Garamond', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        brand: {
          50: '#F2F6F3',
          100: '#E2ECE6',
          200: '#C4D4CA',
          300: '#8DA89A',
          400: '#6B8A7A',
          500: '#4A6A5C',
          600: '#3A5A4C',
          700: '#2D4A3E',
          800: '#243D2E',
          900: '#1A2E22',
        },
        beige: {
          50: '#FAF7F2',
          100: '#F5F0E8',
          200: '#F0EAE0',
          300: '#E8E0D4',
          400: '#D8CFC0',
          500: '#C2B8A8',
          600: '#A09888',
          700: '#7D7464',
          800: '#5C5446',
          900: '#3A3428',
        },
        accent: {
          gold: '#C4A45C',
          'gold-light': '#E8DCC0',
          'gold-dark': '#A8883C',
          ruby: '#A84A3A',
          teal: '#4A8A7A',
        },
        ink: {
          DEFAULT: '#4A4A4A',
          muted: '#8A8A8A',
        },
        stone: {
          DEFAULT: '#E0D8CC',
        },
      },
      backgroundImage: {
        'gradient-hero': 'linear-gradient(135deg, #1A2E22 0%, #2D4A3E 50%, #1A2E22 100%)',
        'gradient-gold': 'linear-gradient(135deg, #C4A45C 0%, #D4B46C 100%)',
      },
      boxShadow: {
        'warm': '0 4px 20px rgba(26,46,34,0.04)',
        'elevated': '0 8px 32px rgba(26,46,34,0.06)',
        'gold': '0 4px 20px rgba(196,164,92,0.2)',
      },
      borderRadius: {
        'btn': '6px',
      },
      letterSpacing: {
        'widest-mono': '0.22em',
      },
      fontSize: {
        'h1': ['3.5rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '300' }],
        'h2': ['2.25rem', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '300' }],
        'h3': ['1.5rem', { lineHeight: '1.3', fontWeight: '350' }],
        'caption-mono': ['12px', { lineHeight: '1', letterSpacing: '0.22em', fontWeight: '500' }],
        'btn': ['12px', { lineHeight: '1', letterSpacing: '0.15em' }],
      },
    },
  },
  plugins: [],
}
