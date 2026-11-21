import { defineConfig } from 'vite'
import preact from '@preact/preset-vite'

// The built client is served by Flask from web/ui/ under /static/ui/, so a
// deep link (/artist/..., /set/...) and every asset URL keep working from the
// same origin with the session cookie.
export default defineConfig({
    plugins: [preact()],
    base: '/static/ui/',
    build: {
        outDir: '../web/ui',
        emptyOutDir: true,
    },
    server: {
        allowedHosts: ["vite.flufi.uk"],
        proxy: { '/api': 'http://127.0.0.1:8000' },
    },
})
