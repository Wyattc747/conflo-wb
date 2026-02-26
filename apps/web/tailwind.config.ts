import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1B2A4A',
          50: '#E8EBF0',
          100: '#D1D7E1',
          200: '#A3AFC3',
          300: '#7587A5',
          400: '#485F87',
          500: '#1B2A4A',
          600: '#16223B',
          700: '#101A2D',
          800: '#0B111E',
          900: '#05090F',
        },
        accent: {
          DEFAULT: '#2E75B6',
          50: '#E9F0F8',
          100: '#D3E1F1',
          200: '#A7C3E3',
          300: '#7BA5D5',
          400: '#4F87C7',
          500: '#2E75B6',
          600: '#255E92',
          700: '#1C476D',
          800: '#133049',
          900: '#091824',
        },
      },
    },
  },
  plugins: [],
};

export default config;
