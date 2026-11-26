import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";

// Playwright runs against the *built* client (`web/ui/`), served by Vite preview
// from the same `/static/ui/` base the Flask app uses in production.
const uiDir = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
    testDir: "./e2e",
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 1 : 0,
    // Each responsive test visits every route at several viewport sizes.
    timeout: 240_000,
    expect: { timeout: 10_000 },
    reporter: [
        ["list"],
        ["html", { outputFolder: "playwright-report", open: "never" }],
    ],
    use: {
        baseURL: "http://127.0.0.1:4173",
        browserName: "chromium",
        screenshot: "only-on-failure",
    },
    outputDir: "test-results",
    webServer: {
        command: "npm run preview -- --host 127.0.0.1 --port 4173 --strictPort",
        url: "http://127.0.0.1:4173/static/ui/",
        cwd: uiDir,
        reuseExistingServer: !process.env.CI,
        timeout: 60_000,
    },
});
