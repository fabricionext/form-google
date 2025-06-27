import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: 'app/peticionador/static/dist',
    rollupOptions: {
      input: {
        'formulario-dinamico': resolve(__dirname, 'src/formulario-dinamico.js'),
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name]-[hash].js',
        assetFileNames: '[name].[ext]'
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/peticionador': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})