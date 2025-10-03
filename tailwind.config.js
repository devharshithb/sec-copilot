module.exports = {
  content: [
    "./app/ui/web/**/*.html",
    "./app/ui/web/**/*.js"
  ],
  theme: {
    extend: {
      fontFamily: {
        mont: ['Montserrat', 'ui-sans-serif', 'system-ui'],
      },
      colors: {
        brand: {
          red: "#FF4B2B",
          pink: "#FF416C"
        }
      },
      boxShadow: {
        card: "0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22)"
      }
    },
  },
  plugins: []
};
