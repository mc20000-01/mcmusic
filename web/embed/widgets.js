(() => {
  const SCRIPT = document.currentScript || Array.from(document.scripts).find(s => (s.src||'').includes('/static/embed/widgets.js'));
  const BASE = (SCRIPT && (SCRIPT.dataset.mcmusicBase || SCRIPT.getAttribute('data-mcmusic-base'))) || (SCRIPT ? new URL('.', SCRIPT.src).origin : location.origin);
  /* flufi v3 palettes: one ink surface scale, one interaction accent. */
  const THEMES = {
    dusk:   { bg:'#08060d', bg2:'#100c18', fg:'#ffffff', dim:'#948aa6', line:'#1f1830', accent:'#a06bff' },
    paper:  { bg:'#f6f3fa', bg2:'#ece7f4', fg:'#08060d', dim:'#6a6178', line:'#d8d0e4', accent:'#7040c8' },
    ink:    { bg:'#000000', bg2:'#0d0a13', fg:'#ffffff', dim:'#948aa6', line:'#251d35', accent:'#b888ff' },
    tide:   { bg:'#080d14', bg2:'#0d1520', fg:'#f4f7ff', dim:'#8fa0b8', line:'#1f2d40', accent:'#7aa2ff' },
    copper: { bg:'#100b08', bg2:'#181009', fg:'#fff7f0', dim:'#b8a394', line:'#34261a', accent:'#e6a06b' },
    forest: { bg:'#07100c', bg2:'#0b1811', fg:'#f0fff6', dim:'#91ad9d', line:'#1a3527', accent:'#5fd39b' },
    rose:   { bg:'#12080f', bg2:'#1b0c17', fg:'#fff0f8', dim:'#b995aa', line:'#3a1f31', accent:'#ff79b8' },
  };

  /* Colour hooks a host page may set on the tag itself; anything declared out
     there (stylesheet or inline style) beats the theme we resolve here. */
  const VAR_NAMES = ['--mc-bg','--mc-bg2','--mc-fg','--mc-dim','--mc-line','--mc-accent','--mc-accent-soft'];
  const softOf = (c) => `color-mix(in srgb, ${c} 20%, transparent)`;

  /* One full pass of over-long text; the widgets re-render on every poll, so the
     offset is carried over to keep the line moving instead of jumping back. The
     `speed` attribute overrides the 18 s per-instance. */
  const SLIDE_SEC = 18;
  const slideMs = (host) => {
    const n = parseFloat(host.getAttribute('speed') || '');
    return Math.max(3, Math.min(60, n > 0 ? n : SLIDE_SEC)) * 1000;
  };

  /* `demo` renders sample data with no username and no network, so a gallery or
     an offline draft can show the widgets before anyone is playing. */
  const DEMO_COVER = 'data:image/svg+xml,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">'
    + '<rect width="120" height="120" fill="#08060d"/>'
    + '<circle cx="60" cy="60" r="34" fill="none" stroke="#a06bff" stroke-width="2"/>'
    + '<circle cx="60" cy="60" r="5" fill="#a06bff"/></svg>');
  const demoPayload = () => ({
    user: { username: 'demo' },
    listening: true,
    position: 83,
    track: { title: 'Midnight City Lights (Extended Club Mix)', artist: 'The Paper Tigers', album: 'Static & Smoke', duration: 214 },
    cover_url: DEMO_COVER,
    profile_url: '',
  });

  function themeVars(name, accent) {
    const base = (name === 'auto'
      ? (matchMedia && matchMedia('(prefers-color-scheme: light)').matches ? THEMES.paper : THEMES.dusk)
      : (THEMES[name] || THEMES.dusk));
    const a = accent || base.accent;
    return {
      '--mc-bg': base.bg, '--mc-bg2': base.bg2, '--mc-fg': base.fg, '--mc-dim': base.dim,
      '--mc-line': base.line, '--mc-accent': a, '--mc-accent-soft': softOf(a),
    };
  }

  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function fmtTime(sec){
    sec = Math.max(0, Number(sec)||0);
    const m = Math.floor(sec/60), s = Math.floor(sec%60);
    return m + ':' + String(s).padStart(2,'0');
  }

  const sharedCSS = `
  :host{all:initial;display:block;font-family:var(--_font);color:var(--_fg);
    --_radius:var(--mc-radius,var(--radius,10px));
    --_font:var(--mc-font,var(--font-family,Inter,system-ui,-apple-system,"Segoe UI",sans-serif));
    --_bg:var(--mc-bg,var(--back,#08060d));
    --_bg2:var(--mc-bg2,var(--back-raised,#100c18));
    --_fg:var(--mc-fg,var(--text-bright,#ffffff));
    --_dim:var(--mc-dim,var(--text-dim,#948aa6));
    --_line:var(--mc-line,var(--back-border,#1f1830));
    --_accent:var(--mc-accent,var(--accent,#a06bff));
    --_soft:var(--mc-accent-soft,color-mix(in srgb,var(--_accent) 20%,transparent));}
  *,*::before,*::after{box-sizing:border-box}
  .card{position:relative;overflow:hidden;border-radius:var(--_radius);border:1px solid var(--_line);background:var(--_bg)}
  .glow{display:none}
  .row{position:relative;display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:center;padding:14px}
  .cover{width:72px;height:72px;border-radius:var(--_radius);object-fit:cover;background:var(--_bg2);border:1px solid var(--_line)}
  .meta{min-width:0}
  .kicker{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--_accent);margin:0 0 4px}
  .title{font-size:16px;font-weight:600;line-height:1.25;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--_fg)}
  .sub{font-size:13px;color:var(--_dim);margin:4px 0 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .foot{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-top:12px;padding-top:10px;border-top:1px solid var(--_line);font-size:12px;color:var(--_dim)}
  .pill{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:var(--_radius);border:1px solid var(--_line);background:var(--_bg2)}
  .dot{width:7px;height:7px;border-radius:50%;background:var(--_accent);box-shadow:0 0 0 3px var(--_soft)}
  .dot.off{background:var(--_dim);box-shadow:none}
  a{color:var(--_accent);text-decoration:none}
  .turn{grid-template-columns:auto 1fr;gap:16px}
  .platter{position:relative;width:96px;height:96px;border-radius:50%;background:var(--_bg2);border:1px solid var(--_line);display:grid;place-items:center}
  .platter::after{content:"";position:absolute;inset:10px;border-radius:50%;border:1px solid var(--_line)}
  .disc{width:64px;height:64px;border-radius:50%;object-fit:cover;border:1px solid var(--_line)}
  .spindle{position:absolute;width:8px;height:8px;border-radius:50%;background:var(--_accent);box-shadow:0 0 0 2px var(--_bg)}
  .spin{animation:spin 4.5s linear infinite}
  .paused .spin{animation-play-state:paused}
  @keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}
  .bar{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:var(--_radius);border:1px solid var(--_line);background:var(--_bg);min-width:0}
  .bar .cover{width:34px;height:34px}
  .bar .title{font-size:13px}.bar .sub{font-size:11px;margin-top:1px}
  .badge{display:inline-flex;align-items:center;gap:8px;max-width:100%;padding:6px 10px;border-radius:var(--_radius);border:1px solid var(--_line);background:var(--_bg)}
  .badge .cover{width:22px;height:22px}
  .badge .txt{font-size:12px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--_fg)}
  .profile .cover{width:96px;height:96px}
  .profile .title{font-size:18px}
  .progress{margin-top:10px;height:4px;border-radius:var(--_radius);background:var(--_bg2);border:1px solid var(--_line);overflow:hidden}
  .progress > i{display:block;height:100%;background:var(--_accent)}
  .marquee{overflow:hidden;white-space:nowrap}
  .marquee span{display:inline-block;padding-left:100%;animation:mar 14s linear infinite}
  /* over-long text: the line is doubled and slides by exactly one copy so the
     loop is seamless and the start is readable straight away */
  .slide{overflow:hidden;white-space:nowrap}
  .slide > span{display:inline-block;animation:slide ${SLIDE_SEC}s linear infinite}
  .slide:hover > span{animation-play-state:paused}
  .title.slide,.sub.slide,.txt.slide{text-overflow:clip}
  @keyframes slide{from{transform:translateX(0)}to{transform:translateX(-50%)}}
  @keyframes mar{from{transform:translateX(0)}to{transform:translateX(-100%)}}
  .compact .row{padding:10px;gap:10px}
  .compact .cover{width:54px;height:54px}
  .compact .platter{width:72px;height:72px}
  .compact .disc{width:48px;height:48px}
  .compact .title{font-size:14px}
  .compact .sub{font-size:12px}
  `;

  class BaseWidget extends HTMLElement {
    constructor(){ super(); this.attachShadow({mode:'open'}); this._timer=null; this._data=null; this._mine=new Set(); }
    connectedCallback(){ this.render(true); this.start(); }
    disconnectedCallback(){ this.stop(); }
    static get observedAttributes(){ return ['user','theme','accent','compact','refresh','maxlen','speed','demo','mode']; }
    attributeChangedCallback(){ this.render(true); this.start(); }
    _demo(){ return !this.getAttribute('user') && this.hasAttribute('demo'); }
    start(){ this.stop(); if(this._demo()){ this.fetch(); return; } const sec = Math.max(5, parseInt(this.getAttribute('refresh')||'12',10)||12); this._timer = setInterval(()=>this.fetch(), sec*1000); this.fetch(); }
    stop(){ if(this._timer){ clearInterval(this._timer); this._timer=null; } }
    async fetch(){
      const user = this.getAttribute('user');
      if(!user && this.hasAttribute('demo')){ this._data = demoPayload(); this.render(); return; }
      if(!user){ this._data={error:'missing user'}; this.render(); return; }
      try{
        const res = await fetch(`${BASE}/api/public/now/${encodeURIComponent(user)}`, {headers:{'accept':'application/json'}});
        this._data = res.ok ? await res.json() : {error:'unavailable'};
      }catch(e){ this._data={error:'offline'}; }
      this.render();
    }
    applyVars(){
      /* Drop only the defaults we wrote last time (never a style="" the page
         author put on the tag), then read back what the host resolves to and
         fill in only the variables nobody outside declared. */
      for(const k of this._mine) this.style.removeProperty(k);
      this._mine.clear();
      const outside = getComputedStyle(this);
      const vars = themeVars(this.getAttribute('theme')||'dusk', this.getAttribute('accent'));
      const accent = outside.getPropertyValue('--mc-accent').trim() || vars['--mc-accent'];
      for(const k of VAR_NAMES){
        if(outside.getPropertyValue(k).trim()) continue;
        this.style.setProperty(k, k === '--mc-accent-soft' ? softOf(accent) : vars[k]);
        this._mine.add(k);
      }
      if(this.hasAttribute('compact')) this.classList.add('compact'); else this.classList.remove('compact');
      /* after the renderer has written its markup, not before */
      queueMicrotask(() => this.applyScrollLimit());
    }
    /* `maxlen` characters is the longest run of text shown whole: past that the
       line scrolls like the ticker instead of ending in an ellipsis. The text is
       doubled inside the marquee so the loop has something to lead with. */
    applyScrollLimit(root = this.shadowRoot){
      const max = parseInt(this.getAttribute('maxlen')||'0', 10) || 0;
      if(!root || max <= 0 || typeof root.querySelectorAll !== 'function') return;
      const lines = [...root.querySelectorAll('.title,.sub,.txt')];
      const key = lines.map(el => String(el.textContent||'').trim()).join('\u0000');
      const ms = slideMs(this);
      const now = Date.now();
      if(key !== this._slideKey){ this._slideKey = key; this._slideStart = now; }
      const offset = Math.max(0, now - (this._slideStart || now));
      for(const el of lines){
        if(el.classList.contains('slide')) continue;
        const text = String(el.textContent||'').trim();
        if(text.length <= max) continue;
        el.innerHTML = `<span style="animation-duration:${ms/1000}s;animation-delay:-${((offset % ms) / 1000).toFixed(2)}s">`
          + `${esc(text)} &nbsp; • &nbsp; ${esc(text)} &nbsp; • &nbsp;</span>`;
        el.classList.add('slide');
      }
    }
    _stateText(d){
      if(!d || d.error) return !d ? 'Loading…' : d.error;
      return d.listening ? 'Listening now' : (d.track ? 'Paused' : 'Quiet right now');
    }
  }

  class McNow extends BaseWidget {
    render(){
      this.applyVars();
      const d = this._data;
      if(!d || d.error){
        const msg = !d ? 'Loading…' : esc(d.error);
        this.shadowRoot.innerHTML = `<style>${sharedCSS}</style><div class="card"><div class="row"><div class="meta"><p class="kicker">mcmusic</p><p class="title">${msg}</p></div></div></div>`; return;
      }
      const t = d.track || {};
      const title = t.title || 'Nothing playing right now';
      const sub = t.artist ? `${esc(t.artist)}${t.album ? ' · '+esc(t.album) : ''}` : 'mcmusic';
      const state = this._stateText(d);
      const dur = Number(t.duration||0), pos = Math.min(dur||Infinity, Number(d.position||0));
      const pct = dur > 0 ? Math.max(0, Math.min(100, (pos/dur)*100)) : 0;
      this.shadowRoot.innerHTML = `<style>${sharedCSS}</style>
        <div class="card">
          <div class="glow"></div>
          <div class="row">
            <img class="cover" src="${esc(d.cover_url||'')}" alt="">
            <div class="meta">
              <p class="kicker">${esc(d.user?.username||'mcmusic')}</p>
              <p class="title">${esc(title)}</p>
              <p class="sub">${sub}</p>
              ${dur>0 ? `<div class="progress"><i style="width:${pct}%"></i></div><div class="foot" style="margin-top:6px"><span>${fmtTime(pos)}</span><span>${fmtTime(dur)}</span></div>` : ''}
              <div class="foot" style="${dur>0?'margin-top:6px':''}">
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
      const sub = t.artist ? `${esc(t.artist)}${t.album ? ' · '+esc(t.album) : ''}` : 'Drop the needle when something plays';
      const state = d.listening ? 'Spinning' : (d.track ? 'Paused' : 'Idle');
      this.shadowRoot.innerHTML = `<style>${sharedCSS}</style>
        <div class="card ${d.listening ? '' : 'paused'}">
          <div class="glow"></div>
          <div class="row turn">
            <div class="platter"><img class="disc spin" src="${esc(d.cover_url||'')}" alt=""><div class="spindle"></div></div>
            <div class="meta">
              <p class="kicker">${esc(d.user?.username||'mcmusic')} · turntable</p>
              <p class="title">${esc(title)}</p>
              <p class="sub">${sub}</p>
              <div class="foot">
                <span class="pill"><span class="dot ${d.listening?'':'off'}"></span>${esc(state)}</span>
                ${d.profile_url ? `<a href="${esc(d.profile_url)}" target="_blank" rel="noopener">Open</a>` : ''}
              </div>
            </div>
          </div>
        </div>`;
    }
  }

  class McBar extends BaseWidget {
    render(){
      this.applyVars();
      const d = this._data;
      if(!d || d.error){
        const msg = !d ? 'Loading…' : esc(d.error);
        this.shadowRoot.innerHTML = `<style>${sharedCSS}</style><div class="bar"><span class="txt">${msg}</span></div>`; return;
      }
      const t = d.track || {};
      const title = esc(t.title || 'Nothing playing');
      const sub = esc(t.artist ? t.artist : (d.user?.username || 'mcmusic'));
      this.shadowRoot.innerHTML = `<style>${sharedCSS}</style>
        <a class="bar" href="${esc(d.profile_url||'#')}" target="_blank" rel="noopener">
          <img class="cover" src="${esc(d.cover_url||'')}" alt="">
          <span class="dot ${d.listening?'':'off'}"></span>
          <div class="meta"><p class="title">${title}</p><p class="sub">${sub}</p></div>
        </a>`;
    }
  }

  class McBadge extends BaseWidget {
    render(){
      this.applyVars();
      const d = this._data;
      if(!d || d.error){
        const msg = !d ? 'Loading…' : esc(d.error);
        this.shadowRoot.innerHTML = `<style>${sharedCSS}</style><span class="badge"><span class="dot off"></span><span class="txt">${msg}</span></span>`; return;
      }
      const t = d.track || {};
      const txt = t.title ? `${t.artist ? t.artist+' — ' : ''}${t.title}` : `${d.user?.username||'mcmusic'}: quiet`;
      this.shadowRoot.innerHTML = `<style>${sharedCSS}</style>
        <a class="badge" href="${esc(d.profile_url||'#')}" target="_blank" rel="noopener" title="${esc(txt)}">
          <span class="dot ${d.listening?'':'off'}"></span>
          <img class="cover" src="${esc(d.cover_url||'')}" alt="">
          <span class="txt">${esc((d.listening?'Listening: ':'') + txt)}</span>
        </a>`;
    }
  }

  class McCard extends BaseWidget {
    render(){
      this.applyVars();
      const d = this._data;
      if(!d || d.error){
        const msg = !d ? 'Loading…' : esc(d.error);
        this.shadowRoot.innerHTML = `<style>${sharedCSS}</style><div class="card"><div class="row profile"><div class="meta"><p class="kicker">mcmusic</p><p class="title">${msg}</p></div></div></div>`; return;
      }
      const t = d.track || {};
      const title = t.title || 'Nothing playing right now';
      const sub = t.artist ? `${esc(t.artist)}${t.album ? ' · '+esc(t.album) : ''}` : 'Public listening profile';
      const state = this._stateText(d);
      this.shadowRoot.innerHTML = `<style>${sharedCSS}</style>
        <div class="card">
          <div class="glow"></div>
          <div class="row profile">
            <img class="cover" src="${esc(d.cover_url||'')}" alt="">
            <div class="meta">
              <p class="kicker">mcmusic profile</p>
              <p class="title">${esc(d.user?.username||'mcmusic')}</p>
              <p class="sub">${esc(title)}</p>
              <p class="sub" style="margin-top:2px">${sub}</p>
              <div class="foot">
                <span class="pill"><span class="dot ${d.listening?'':'off'}"></span>${esc(state)}</span>
                ${d.profile_url ? `<a href="${esc(d.profile_url)}" target="_blank" rel="noopener">Open profile</a>` : ''}
              </div>
            </div>
          </div>
        </div>`;
    }
  }

  class McMarquee extends BaseWidget {
    render(){
      this.applyVars();
      const d = this._data;
      if(!d || d.error){
        const msg = !d ? 'Loading…' : esc(d.error);
        this.shadowRoot.innerHTML = `<style>${sharedCSS}</style><div class="bar"><div class="meta marquee"><span>${msg}</span></div></div>`; return;
      }
      const t = d.track || {};
      const text = t.title ? `${d.user?.username||'mcmusic'} ${d.listening?'is listening to':'paused'} ${t.artist ? t.artist+' — ' : ''}${t.title}` : `${d.user?.username||'mcmusic'} is quiet right now`;
      this.shadowRoot.innerHTML = `<style>${sharedCSS}</style>
        <a class="bar" href="${esc(d.profile_url||'#')}" target="_blank" rel="noopener">
          <span class="dot ${d.listening?'':'off'}"></span>
          <div class="meta marquee"><span>${esc(text)} &nbsp; • &nbsp; ${esc(text)} &nbsp; • &nbsp;</span></div>
        </a>`;
    }
  }

  function define(tag, cls){ if(!customElements.get(tag)) customElements.define(tag, cls); }
  /* A constructor can only be registered under one tag name — defining the same
     class for a second name throws NotSupportedError and used to abort every
     definition after it, so the aliases get their own thin subclasses. */
  function defineAlias(tag, cls){ if(!customElements.get(tag)) customElements.define(tag, class extends cls {}); }
  define('mcmusic-now', McNow);
  define('mcmusic-turntable', McTurntable);
  define('mcmusic-bar', McBar);
  define('mcmusic-badge', McBadge);
  define('mcmusic-card', McCard);
  define('mcmusic-marquee', McMarquee);
  defineAlias('mcmusic-now-playing', McNow);
  defineAlias('mcmusic-profile', McCard);
  defineAlias('mcmusic-ticker', McMarquee);
  window.__mcWidgetsScan = () => {
    // custom elements upgrade automatically; hook reserved for future dynamic mounts
  };
})();
