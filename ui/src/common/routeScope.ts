/** Which anchors the SPA router may intercept.

 * preact-iso tests each same-origin anchor's raw `href` against this RegExp.
 * Only client-owned paths should match: server-owned downloads, health checks,
 * OAuth authorize endpoints, static assets, embeds and icon files must trigger
 * a real document request so the browser reaches Flask. `/auth`, `/forgot`,
 * `/reset`, `/not-allowed` and every normal shell page stay in scope.
 */
const SERVER_SEGMENTS = [
    "/api",
    "/health",
    "/apps",
    "/get",
    "/downloads",
    "/embed",
    "/embeds",
    "/video-cache",
    "/u",
    "/static",
    "/manifest\\.webmanifest",
    "/sw\\.js",
];

const SERVER_PREFIXES = SERVER_SEGMENTS
    .map((path) => `${path}(?=[/?#]|$)`)
    .join("|");

const ROOT_ICONS = [
    "favicon\\.ico",
    "apple-touch-icon\\.png",
    "icon(?:-[^/]*)?\\.(?:png|svg)",
].join("|");

export const SPA_SCOPE = new RegExp(
    `^(?!(?:${SERVER_PREFIXES}|/(?:${ROOT_ICONS})(?=[/?#]|$)))`,
);
