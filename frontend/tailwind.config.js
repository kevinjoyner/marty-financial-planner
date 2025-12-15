/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        // Stripe-like Palette
        primary: '#635bff', 
        secondary: '#5469d4',
        slate: {
            50: '#f8f9fa',
            100: '#f1f3f5', 
            200: '#e9ecef',
            800: '#32325d',
            900: '#212529',
        }
      },
      boxShadow: {
        'soft': '0 2px 5px -1px rgba(50, 50, 93, 0.25), 0 1px 3px -1px rgba(0, 0, 0, 0.3)',
      }
    },
  },
  plugins: [],
}
