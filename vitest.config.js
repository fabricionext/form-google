import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['src/tests/setup.js'],

    // CONFIGURAÇÃO DE COBERTURA - FASE 5 QDD (Meta: ≥85%)
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',

      // THRESHOLDS PARA FASE 5 - QUALITY-DRIVEN DEVELOPMENT
      thresholds: {
        global: {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85,
        },
      },

      // Incluir apenas código fonte
      include: [
        'src/components/**/*.vue',
        'src/composables/**/*.js',
        'src/stores/**/*.js',
        'src/services/**/*.js',
        'src/utils/**/*.js',
      ],

      // Excluir arquivos de teste e configuração
      exclude: [
        'src/tests/**',
        'src/**/*.test.js',
        'src/**/*.spec.js',
        '**/*.config.js',
        '**/node_modules/**',
      ],
    },

    // Performance e timeout
    testTimeout: 10000,
    hookTimeout: 10000,

    // Reporters para CI/CD
    reporters: ['verbose', 'json', 'html'],
  },

  // Resolver aliases para importações
  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname,
      '~': new URL('./src', import.meta.url).pathname,
    },
  },
});
