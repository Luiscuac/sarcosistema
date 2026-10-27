import eslint from '@eslint/js'

export default [
  {
    ignores: ['dist/**'],
  },
  {
    files: ['src/**/*.{js,jsx}'],
    ...eslint.configs.recommended,
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: {
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        URL: 'readonly',
        crypto: 'readonly',
        fetch: 'readonly',
        FormData: 'readonly',
        navigator: 'readonly',
        MediaRecorder: 'readonly',
        Blob: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
      },
    },
  },
  {
    files: ['src/**/*.jsx'],
    // ESLint core does not count JSX element names as variable references.
    rules: { 'no-unused-vars': 'off' },
  },
]
