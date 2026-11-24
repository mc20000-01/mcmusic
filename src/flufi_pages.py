"""Shared shell for the standalone HTML pages.

The web client itself is flufi-ui. These few server-rendered pages use the
same generated stylesheet and the same component class names, so profiles,
embeds, OAuth callbacks and the build fallback all look like the v3 client
instead of carrying their own miniature design systems.
"""
from __future__ import annotations

from html import escape

from flask import Response

FLUFI_CSS = "/static/ui/flufi-ui.css"

# Layout only. Colours, controls, spacing and radii come from flufi-ui.
_LAYOUT_CSS = r"""
.flufi-page{min-height:100vh;display:flex;flex-direction:column;align-items:center;
  gap:18px;padding:32px 18px 64px}
.flufi-page > *{width:min(100%,680px)}
.flufi-page .text{line-height:1.55}
.flufi-page .lead{max-width:62ch;color:var(--text-dim)}
.flufi-page .label{color:var(--text-dim);font-size:var(--font-size-small)}
.flufi-page .muted{color:var(--text-dim)}
.flufi-page .seperator{width:100%;height:1px;background:var(--back-border)}
.flufi-page .profile-head{display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.flufi-page .profile-cover{width:96px;height:96px;object-fit:cover;flex:0 0 auto;
  background:var(--prim);border:1px solid var(--back-border);
  border-radius:var(--radius,10px)}
.flufi-page .profile-track{font-size:var(--font-size-big);color:var(--text-bright);
  font-weight:600;line-height:1.25}
.flufi-page .profile-foot{display:flex;align-items:center;justify-content:space-between;
  gap:12px;flex-wrap:wrap;padding-top:12px;border-top:1px solid var(--back-border)}
.flufi-page .profile-url{overflow-wrap:anywhere;color:var(--text-dim)}
.flufi-page .selectable{user-select:text}
.flufi-page pre{margin:0;padding:12px 13px;overflow:auto;user-select:text;background:var(--prim);
  border:1px solid var(--prim-border);border-radius:var(--radius,10px);
  color:var(--text);font-family:var(--font-family-mono);font-size:12.5px;line-height:1.6}
.flufi-page code{font-family:var(--font-family-mono);font-size:.92em;color:var(--text)}
.flufi-page pre code{background:none;padding:0}
.flufi-page .link-form{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:14px}
.flufi-page .link-form .input{min-width:min(100%,230px)}
@media(max-width:520px){
  .flufi-page{padding:20px 12px 48px}
  .flufi-page .profile-cover{width:72px;height:72px}
}
"""


def flufi_document(title, body, *, description="", css="", head=""):
    """Return a complete flufi-styled HTML document as a string."""
    meta = ""
    if description:
        safe = escape(description, quote=True)
        meta = (
            f'<meta name="description" content="{safe}">'
            f'<meta property="og:description" content="{safe}">'
        )
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · mcmusic</title>
{meta}
<link rel="stylesheet" href="{FLUFI_CSS}">
<style>{_LAYOUT_CSS}{css}</style>
{head}
</head><body><div class="flufi-page">{body}</div></body></html>"""


def flufi_page(title, body, *, status=200, description="", css="", head="", headers=None):
    """Return a flufi-styled HTML response for a standalone page."""
    resp = Response(
        flufi_document(title, body, description=description, css=css, head=head),
        status=status,
        mimetype="text/html",
    )
    if headers:
        resp.headers.update(headers)
    return resp
