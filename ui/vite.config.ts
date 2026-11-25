import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import preact from '@preact/preset-vite'

// Every bare lucide-preact import (app code and flufi-ui internals) goes
// through the shared registry so icon width/fill settings apply everywhere.
const lucideRegistry = fileURLToPath(new URL('./src/common/lucide.tsx', import.meta.url))

// The built client is served by Flask from web/ui/ under /static/ui/, so a
// deep link (/artist/..., /set/...) and every asset URL keep working from the
// same origin with the session cookie.
export default defineConfig({
    plugins: [preact()],
    resolve: {
        alias: [{ find: /^lucide-preact$/, replacement: lucideRegistry }],
    },
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
