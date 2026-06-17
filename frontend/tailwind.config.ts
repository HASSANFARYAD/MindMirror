import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        mindmirror: {
          bg: "#0D0B1A",
          surface: "#1A1730",
          primary: "#F5F3FF",
          secondary: "#9E9CB8",
          muted: "#5E5A7A",
          violet: "#7C3AED",
          pink: "#EC4899",
          lavender: "#A78BFA",
        },
      },
      fontFamily: {
        sans: ["var(--font-plus-jakarta-sans)", "Inter", "system-ui", "sans-serif"],
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "0% 50%" },
          "100%": { backgroundPosition: "100% 50%" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
