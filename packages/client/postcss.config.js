// Tailwind v4 moved its PostCSS plugin out of the `tailwindcss` package into
// `@tailwindcss/postcss`. Pointing `tailwindcss: {}` at the main package throws
// "trying to use `tailwindcss` directly as a PostCSS plugin" (see PR #310).
// autoprefixer is retained for the project's own hand-written CSS; Tailwind v4
// handles vendor prefixing for its own output internally.
export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}
