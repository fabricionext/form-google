import js from '@eslint/js';
import { defineConfig } from 'eslint/config';

export default defineConfig([
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: 'module',
      globals: {
        // Variáveis globais do navegador
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        confirm: 'readonly',
        fetch: 'readonly',
        FormData: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        alert: 'readonly',
        requestAnimationFrame: 'readonly',
        URLSearchParams: 'readonly',
        localStorage: 'readonly',
        location: 'readonly',
        self: 'readonly',
        TextEncoder: 'readonly',
        // Variáveis globais específicas do projeto
        IMask: 'readonly',
        EVALEX: 'readonly',
        EVALEX_TRUSTED: 'readonly',
        CONSOLE_MODE: 'readonly',
        SECRET: 'readonly',
      },
    },
    rules: {
      // Regras personalizadas
      'no-unused-vars': 'warn',
      'no-undef': 'error',
      'no-console': 'off', // Permitir console.log em desenvolvimento
      'prefer-const': 'warn',
      'no-var': 'error',
    },
    ignores: [
      'node_modules/**',
      'venv/**',
      '.venv/**',
      '**/site-packages/**',
      '**/*.min.js',
      '**/debugger.js',
      '**/coverage_html.js',
    ],
  },
]);
