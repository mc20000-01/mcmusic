(() => {
  const SCRIPT = document.currentScript;
  const BASE = (SCRIPT && (SCRIPT.dataset.mcmusicBase || SCRIPT.getAttribute('data-mcmusic-base'))) || (SCRIPT ? new URL('.', SCRIPT.src).origin : location.origin);
  const THEMES = {
    dusk:   { bg:'#151022', bg2:'#08060d', fg:'#f2ecff', dim:'#a89ec6', line:'#332a4d', accent:'#a06bff' },
    paper:  { bg:'#fbf7ee', bg2:'#f4efe4', fg:'#241d14', dim:'#6d6151', line:'#bfb098', accent:'#b4531f' },
    ink:    { bg:'#121214', bg2:'#050505', fg:'#f5f5f5', dim:'#8f8f96', line:'#34343b', accent:'#d7d7de' },
    tide:   { bg:'#18262c', bg2:'#0e161a', fg:'#e4eef1', dim:'#8ba3ab', line:'#33505a', accent:'#6fb3c4' },
    copper: { bg:'#2b1a16', bg2:'#1a0f0d', fg:'#f6e7df', dim:'#b2928a', line:'#553229', accent:'#e08a5f' },
    forest: { bg:'#15261d', bg2:'#0b1410', fg:'#e7f3ec', dim:'#95b2a2', line:'#2f4d3d', accent:'#6fcf97' },
    rose:   { bg:'#2a1b23', bg2:'#171015', fg:'#f7ebf1', dim:'#c2a6b4', line:'#523646', accent:'#e58ab2' },
  };

  function themeVars(name, accent) {
    const base = (name === 'auto'
      ? (matchMedia && matchMedia('(prefers-color-scheme: light)').matches ? THEMES.paper : THEMES.dusk)
      : (THEMES[name] || THEMES.dusk));
    const a = accent || base.accent;
    return {
      '--mc-bg': base.bg, '--mc-bg2': base.bg2, '--mc-fg': base.fg, '--mc-dim': base.dim,
      '--mc-line': base.line, '--mc-accent': a, '--mc-accent-soft': a + '33',
    };
  }

  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

  const sharedCSS = `
  :host{all:initial;display:block;font-family:var(--mc-font,Inter,system-ui,-apple-system,Segoe UI,sans-serif);color:var(--mc-fg);--mc-radius:18px;}
  *,*::before,*::after{box-sizing:border-box}
  .card{position:relative;overflow:hidden;border-radius:var(--mc-radius);border:1px solid color-mix(in srgb,var(--mc-line) 70%, transparent);background:linear-gradient(180deg,color-mix(in srgb,var(--mc-bg) 92%, transparent),color-mix(in srgb,var(--mc-bg2) 96%, transparent));box-shadow:0 12px 30px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.08);backdrop-filter:blur(14px) saturate(140%);-webkit-backdrop-filter:blur(14px) saturate(140%);}
  .glow{position:absolute;inset:-40% -20% auto auto;width:70%;height:140%;background:radial-gradient(circle at 30% 30%, var(--mc-accent-soft), transparent 60%);pointer-events:none;}
  .row{position:relative;display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:center;padding:14px;}
  .cover{width:72px;height:72px;border-radius:14px;object-fit:cover;background:color-mix(in srgb,var(--mc-bg2) 80%, #000);border:1px solid color-mix(in srgb,var(--mc-line) 70%, transparent);box-shadow:0 8px 18px rgba(0,0,0,.25);}
  .meta{min-width:0}
  .kicker{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--mc-accent);margin:0 0 4px}
  .title{font-size:16px;font-weight:700;line-height:1.2;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .sub{font-size:13px;color:var(--mc-dim);margin:4px 0 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .foot{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-top:10px;font-size:12px;color:var(--mc-dim)}
  .pill{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:999px;border:1px solid color-mix(in srgb,var(--mc-line) 70%, transparent);background:color-mix(in srgb,var(--mc-bg) 60%, transparent)}
  .dot{width:7px;height:7px;border-radius:50%;background:var(--mc-accent);box-shadow:0 0 0 4px var(--mc-accent-soft)}
  .dot.off{background:var(--mc-dim);box-shadow:none}
  a{color:inherit;text-decoration:none}
  .turn{grid-template-columns:auto 1fr;gap:16px}
  .platter{position:relative;width:96px;height:96px;border-radius:50%;background:radial-gradient(circle at 50% 50%, #222 0 18%, #0b0b0b 19% 22%, #1a1a1a 23% 35%, #0f0f0f 36% 48%, #171717 49% 62%, #0d0d0d 63% 100%);box-shadow:inset 0 0 0 1px rgba(255,255,255,.08), 0 10px 24px rgba(0,0,0,.35);display:grid;place-items:center}
  .platter::after{content:"";position:absolute;inset:10px;border-radius:50%;border:1px solid rgba(255,255,255,.05)}
  .disc{width:64px;height:64px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,.2);box-shadow:0 0 0 4px rgba(0,0,0,.35)}
  .spindle{position:absolute;width:8px;height:8px;border-radius:50%;background:linear-gradient(#fff,#999);box-shadow:0 0 0 2px rgba(0,0,0,.5)}
  .spin{animation:spin 4.5s linear infinite}
  .paused .spin{animation-play-state:paused}
  @keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}
  .compact .row{padding:10px;gap:10px}
  .compact .cover{width:54px;height:54px;border-radius:12px}
  .compact .platter{width:72px;height:72px}
  .compact .disc{width:48px;height:48px}
  .compact .title{font-size:14px}
  .compact .sub{font-size:12px}
  `;

  class BaseWidget extends HTMLElement {
    constructor(){ super(); this.attachShadow({mode:'open'}); this._timer=null; this._data=null; }
    connectedCallback(){ this.render(true); this.start(); }
    disconnectedCallback(){ this.stop(); }
    static get observedAttributes(){ return ['user','theme','accent','compact','refresh']; }
    attributeChangedCallback(){ this.render(true); this.start(); }
    start(){ this.stop(); const sec = Math.max(5, parseInt(this.getAttribute('refresh')||'15',10)||15); this._timer = setInterval(()=>this.fetch(), sec*1000); this.fetch(); }
    stop(){ if(this._timer){ clearInterval(this._timer); this._timer=null; } }
    async fetch(){
      const user = this.getAttribute('user');
      if(!user){ this._data={error:'missing user'}; this.render(); return; }
      try{
        const res = await fetch(`${BASE}/api/public/now/${encodeURIComponent(user)}`, {headers:{'accept':'application/json'}});
        this._data = res.ok ? await res.json() : {error:'unavailable'};
      }catch(e){ this._data={error:'offline'}; }
      this.render();
    }
    applyVars(){
      const vars = themeVars(this.getAttribute('theme')||'dusk', this.getAttribute('accent'));
      for(const k in vars) this.style.setProperty(k, vars[k]);
      if(this.hasAttribute('compact')) this.classList.add('compact'); else this.classList.remove('compact');
    }
  }

  class McNow extends BaseWidget {
    render(){
      this.applyVars();
      const d = this._data;
      if(!d){
        this.shadowRoot.innerHTML = `<style>${sharedCSS}</style><div class="card"><div class="row"><div class="meta"><p class="kicker">mcmusic</p><p class="title">Loading…</p></div></div></div>`; return;
      }
      if(d.error){
        this.shadowRoot.innerHTML = `<style>${sharedCSS}</style><div class="card"><div class="row"><div class="meta"><p class="kicker">mcmusic</p><p class="title">${esc(d.error)}</p></div></div></div>`; return;
      }
      const t = d.track || {};
      const title = t.title || 'Nothing playing right now';
      const sub = t.artist ? `${t.artist}${t.album ? ' · '+t.album : ''}` : 'mcmusic';
      const state = d.listening ? 'Listening now' : (d.track ? 'Paused' : 'Quiet right now');
      this.shadowRoot.innerHTML = `<style>${sharedCSS}</style>
        <div class="card">
          <div class="glow"></div>
          <div class="row">
            <img class="cover" src="${esc(d.cover_url||'')}" alt="">
            <div class="meta">
              <p class="kicker">${esc(d.user?.username||'mcmusic')}</p>
              <p class="title">${esc(title)}</p>
              <p class="sub">${esc(sub)}</p>
              <div class="foot">
                <span class="pill"><span class="dot ${d.listening?'':'off'}"></span>${esc(state)}</span>
                ${d.profile_url ? `<a href="${esc(d.profile_url)}" target="_blank" rel="noopener">Open</a>` : ''}
              </div>
            </div>
          </div>
        </div>`;
    }
  }

  class McTurntable extends BaseWidget {
    render(){
      this.applyVars();
      const d = this._data;
      if(!d || d.error){
        const msg = !d ? 'Loading…' : esc(d.error);
        this.shadowRoot.innerHTML = `<style>${sharedCSS}</style><div class="card"><div class="row turn"><div class="platter paused"><div class="spindle"></div></div><div class="meta"><p class="kicker">mcmusic</p><p class="title">${msg}</p></div></div></div>`; return;
      }
      const t = d.track || {};
      const title = t.title || 'Nothing playing right now';
      const sub = t.artist ? `${t.artist}${t.album ? ' · '+t.album : ''}` : 'Drop the needle when something plays';
      const state = d.listening ? 'Spinning' : (d.track ? 'Paused' : 'Idle');
      this.shadowRoot.innerHTML = `<style>${sharedCSS}</style>
        <div class="card ${d.listening ? '' : 'paused'}">
          <div class="glow"></div>
          <div class="row turn">
            <div class="platter"><img class="disc spin" src="${esc(d.cover_url||'')}" alt=""><div class="spindle"></div></div>
            <div class="meta">
              <p class="kicker">${esc(d.user?.username||'mcmusic')} · turntable</p>
              <p class="title">${esc(title)}</p>
              <p class="sub">${esc(sub)}</p>
              <div class="foot">
                <span class="pill"><span class="dot ${d.listening?'':'off'}"></span>${esc(state)}</span>
                ${d.profile_url ? `<a href="${esc(d.profile_url)}" target="_blank" rel="noopener">Open</a>` : ''}
              </div>
            </div>
          </div>
        </div>`;
    }
  }

  if(!customElements.get('mcmusic-now')) customElements.define('mcmusic-now', McNow);
  if(!customElements.get('mcmusic-now-playing')) customElements.define('mcmusic-now-playing', McNow);
  if(!customElements.get('mcmusic-turntable')) customElements.define('mcmusic-turntable', McTurntable);
})();
