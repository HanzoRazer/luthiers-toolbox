// packages/client/.eslintrc.cjs
// ESLint configuration for Vue 3 + TypeScript

module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:vue/recommended' // eslint-plugin-vue 10 renamed vue3-recommended -> recommended
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    parser: '@typescript-eslint/parser',
    sourceType: 'module'
  },
  plugins: [
    '@typescript-eslint',
    'vue'
  ],
  rules: {
    // Relaxed rules for initial adoption
    '@typescript-eslint/no-explicit-any': 'warn',
    // caughtErrors: 'none' pins the typescript-eslint v6 default; v8 flipped it to 'all'.
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', caughtErrors: 'none' }],
    'vue/multi-word-component-names': 'off',
    'vue/no-v-html': 'warn',

    // Component complexity limits - encourage composable extraction
    // Warn at 300 lines, error at 500 lines
    'max-lines': ['warn', {
      max: 500,
      skipBlankLines: true,
      skipComments: true
    }],

    // Function complexity - encourage smaller, focused functions
    'max-lines-per-function': ['warn', {
      max: 100,
      skipBlankLines: true,
      skipComments: true,
      IIFEs: true
    }]
  },
  ignorePatterns: [
    'dist/',
    'node_modules/',
    '*.config.js',
    '*.config.ts'
  ]
};
