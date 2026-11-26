#!/usr/bin/env node
// Remove third-party font CDN imports from built CSS.
//
// Fonts are bundled locally from @fontsource-variable packages. flufi-ui's
// stylesheet still carries a fonts.googleapis.com @import, so the built CSS is
// sanitised here instead of patching node_modules. This script intentionally
// fails on any remote @import it cannot account for, rather than silently
// shipping a CDN dependency.
import fs from "node:fs";
import path from "node:path";

const ROOT = process.argv[2] || process.cwd();
const allowedFontHosts = /(?:fonts\.googleapis\.com|fonts\.gstatic\.com)/i;
const remoteImport = /@import\s+(?:url\()?\s*["']?https?:\/\/[^"')]+["']?\s*\)?\s*;/gi;

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return walk(full);
    return entry.isFile() && full.endsWith(".css") ? [full] : [];
  });
}

const files = walk(path.join(ROOT, "web/ui"));
let removed = 0;
for (const file of files) {
  const before = fs.readFileSync(file, "utf8");
  const matches = before.match(remoteImport) || [];
  const unexpected = matches.filter(match => !allowedFontHosts.test(match));
  if (unexpected.length) {
    console.error(`${path.relative(ROOT, file)}: unexpected remote @import: ${unexpected.join(" ")}`);
    process.exit(1);
  }
  const after = before.replace(remoteImport, "");
  if (after !== before) {
    fs.writeFileSync(file, after);
    removed += matches.length;
    console.log(`stripped ${matches.length} font CDN import(s) from ${path.relative(ROOT, file)}`);
  }
}
console.log(`strip-font-cdn: checked ${files.length} CSS file(s), removed ${removed} import(s)`);
