/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        dc: {
          rail: '#1e1f22',
          sidebar: '#2b2d31',
          chat: '#313338',
          input: '#383a40',
          hover: '#35373c',
          active: '#404249',
          border: '#3f4147',
          divider: '#26272b',
          text: '#dbdee1',
          muted: '#949ba4',
          bright: '#f2f3f5',
          blurple: '#5865f2',
          blurpleHover: '#4752c4',
          link: '#00a8fc',
          green: '#23a55a',
          yellow: '#f0b232',
          red: '#f23f43',
          mention: '#3c4270',
        },
      },
      fontFamily: {
        sans: ['"gg sans"', 'Whitney', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Consolas', 'monospace'],
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 200ms ease-out',
      },
    },
  },
  plugins: [],
}
