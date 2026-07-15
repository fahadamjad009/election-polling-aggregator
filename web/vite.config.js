import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/election-polling-aggregator/',
  plugins: [react()],
})
