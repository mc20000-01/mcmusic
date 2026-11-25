(() => {
  const SCRIPT = document.currentScript || Array.from(document.scripts).find(s => (s.src||'').includes('/static/embed/widgets.js'));
  const BASE = (SCRIPT && (SCRIPT.dataset.mcmusicBase || SCRIPT.getAttribute('data-mcmusic-base'))) || (SCRIPT ? new URL('.', SCRIPT.src).origin : location.origin);
  /* Five palette families. Bare family ids (and auto/system) follow the
     visitor's light/dark preference; *-light / *-dark pin one half. Older
     names remain aliases so existing embed tags keep their colours. */
  const THEMES = {
    'violet-light': { bg:'#F5F2FF', bg2:'#EDE7FF', surface:'#FFFFFF', surface2:'#F7F4FF', fg:'#08060D', dim:'#473872', dim2:'#6A54AA', line:'#DACDFF', line2:'#CAB8FF', accent:'#9F7EFF' },
    'violet-dark':  { bg:'#171721', bg2:'#222130', surface:'#2A293C', surface2:'#444361', fg:'#FFFFFF', dim:'#AAAAB7', dim2:'#8B8A9D', line:'#35344B', line2:'#605F78', accent:'#9F7EFF' },
    'indigo-light': { bg:'#F2F4FF', bg2:'#E8EBFF', surface:'#FFFFFF', surface2:'#F5F6FF', fg:'#08060D', dim:'#3B4172', dim2:'#5761AA', line:'#CFD5FF', line2:'#BAC3FF', accent:'#8293FF' },
    'indigo-dark':  { bg:'#12171F', bg2:'#1B212D', surface:'#212838', surface2:'#36425B', fg:'#FFFFFF', dim:'#A4A9B5', dim2:'#828999', line:'#2A3346', line2:'#545E73', accent:'#8293FF' },
    'sky-light':    { bg:'#F1F8FE', bg2:'#E7F3FE', surface:'#FFFFFF', surface2:'#F4F9FE', fg:'#08060D', dim:'#385272', dim2:'#527CA9', line:'#CCE5FE', line2:'#B6DAFE', accent:'#7BBDFE' },
    'sky-dark':     { bg:'#182127', bg2:'#222F39', surface:'#2A3A46', surface2:'#455F72', fg:'#FFFFFF', dim:'#ABB7BF', dim2:'#8B9BA7', line:'#354A58', line2:'#607787', accent:'#7BBDFE' },
    'aqua-light':   { bg:'#F1FBFC', bg2:'#E7F9FA', surface:'#FFFFFF', surface2:'#F4FCFD', fg:'#08060D', dim:'#386168', dim2:'#53939A', line:'#CDF3F5', line2:'#B6EDF1', accent:'#7CE0E6' },
    'aqua-dark':    { bg:'#15241C', bg2:'#1F3328', surface:'#263F32', surface2:'#3E6751', fg:'#FFFFFF', dim:'#A8BAB0', dim2:'#87A093', line:'#30503F', line2:'#5A7D6B', accent:'#7CE0E6' },
    'mint-light':   { bg:'#F1FFF5', bg2:'#E7FFEE', surface:'#FFFFFF', surface2:'#F4FFF7', fg:'#08060D', dim:'#386E4C', dim2:'#52A76F', line:'#CCFFDC', line2:'#B6FFCC', accent:'#7BFFA4' },
    'mint-dark':    { bg:'#15241A', bg2:'#1F3425', surface:'#26412E', surface2:'#3E694B', fg:'#FFFFFF', dim:'#A8BBAE', dim2:'#87A28F', line:'#30513A', line2:'#5A7F66', accent:'#7BFFA4' },
    violet: 'system', indigo: 'system', sky: 'system', aqua: 'system', mint: 'system',
    auto: 'system', system: 'system',
    flufi: 'violet-dark', dark: 'violet-dark', dusk: 'violet-dark',
    paper: 'violet-light', light: 'violet-light',
    ink: 'indigo-dark', amoled: 'indigo-dark',
    midnight: 'sky-dark', tide: 'aqua-dark', forest: 'mint-dark',
    rose: 'violet-dark', copper: 'violet-dark', mocha: 'violet-dark',
  };

  /* Colour hooks a host page may set on the tag itself; anything declared out
     there (stylesheet or inline style) beats the theme we resolve here. */
  const VAR_NAMES = ['--mc-bg','--mc-bg2','--mc-fg','--mc-dim','--mc-line','--mc-accent','--mc-accent-text','--mc-accent-soft'];
  const softOf = (c) => `color-mix(in srgb, ${c} 20%, transparent)`;
  /* Accent-as-text needs a readable foreground; the five built-in accents are
     light, while a host-page override can be dark. */
  const readableOn = (c) => {
    const v = String(c || '').trim();
    const hex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(v);
    const rgb = /^rgba?\(\s*(\d+)\s*[,\s]\s*(\d+)\s*[,\s]\s*(\d+)/i.exec(v);
    let parts = null;
    if (hex) {
      const d = hex[1].length === 3 ? hex[1].split('').map(x => x + x).join('') : hex[1];
      parts = [0, 2, 4].map(i => parseInt(d.slice(i, i + 2), 16));
    } else if (rgb) parts = [Number(rgb[1]), Number(rgb[2]), Number(rgb[3])];
    if (!parts) return '#08060D';
    const [r, g, b] = parts.map(n => {
      const x = Math.min(255, Math.max(0, n)) / 255;
      return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
    });
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) > 0.229 ? '#08060D' : '#FFFFFF';
  };

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
    + '<rect width="120" height="120" fill="#171721"/>'
    + '<circle cx="60" cy="60" r="34" fill="none" stroke="#9F7EFF" stroke-width="2"/>'
    + '<circle cx="60" cy="60" r="5" fill="#9F7EFF"/></svg>');
  const demoPayload = () => ({
    user: { username: 'demo' },
    listening: true,
    position: 83,
    track: { title: 'Midnight City Lights (Extended Club Mix)', artist: 'The Paper Tigers', album: 'Static & Smoke', duration: 214 },
    cover_url: DEMO_COVER,
    profile_url: '',
  });

  const preferLight = () => typeof matchMedia === 'function' && matchMedia('(prefers-color-scheme: light)').matches;

  function themeVars(name, accent) {
    const requested = String(name || 'violet').toLowerCase();
    /* auto/system resolve light->violet-light and dark->violet-dark; a bare
       family id resolves to that family's own light/dark half. */
    let key = requested;
    let base = THEMES[key];
    let guard = 0;
    while (typeof base === 'string' && guard++ < 4) {
      if (base === 'system') {
        const family = requested.replace(/-(light|dark)$/, '');
        base = THEMES[preferLight() ? family + '-light' : family + '-dark']
          || THEMES[preferLight() ? 'violet-light' : 'violet-dark'];
      } else {
        base = THEMES[base];
      }
    }
    if (!base || typeof base !== 'object') base = THEMES[preferLight() ? 'violet-light' : 'violet-dark'];
    const a = accent || base.accent;
    return {
      '--mc-bg': base.bg, '--mc-bg2': base.bg2, '--mc-fg': base.fg, '--mc-dim': base.dim,
      '--mc-line': base.line, '--mc-accent': a, '--mc-accent-text': readableOn(a),
      '--mc-accent-soft': softOf(a),
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
    --_bg:var(--mc-bg,var(--back,#171721));
    --_bg2:var(--mc-bg2,var(--back-raised,#222130));
    --_fg:var(--mc-fg,var(--text-bright,#FFFFFF));
    --_dim:var(--mc-dim,var(--text-dim,#AAAAB7));
    --_line:var(--mc-line,var(--back-border,#35344B));
    --_accent:var(--mc-accent,var(--accent,#9F7EFF));
    --_accent-text:var(--mc-accent-text,var(--text-on-light,#08060D));
    --_soft:var(--mc-accent-soft,color-mix(in srgb,var(--_accent) 20%,transparent));}
  *,*::before,*::after{box-sizing:border-box}
  .card{position:relative;overflow:hidden;border-radius:var(--_radius);border:1px solid var(--_line);background:var(--_bg)}
  .glow{display:none}
  .row{position:relative;display:grid;grid-template-columns:auto 1fr;gap:14px;align-items:center;padding:14px}
  .cover{width:72px;height:72px;border-radius:var(--_radius);object-fit:cover;background:var(--_bg2);border:1px solid var(--_line)}
  .meta{min-width:0}
  .kicker{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--_accent-text);margin:0 0 4px}
  .title{font-size:16px;font-weight:600;line-height:1.25;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--_fg)}
  .sub{font-size:13px;color:var(--_dim);margin:4px 0 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .foot{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-top:12px;padding-top:10px;border-top:1px solid var(--_line);font-size:12px;color:var(--_dim)}
  .pill{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:var(--_radius);border:1px solid var(--_line);background:var(--_bg2)}
  .dot{width:7px;height:7px;border-radius:50%;background:var(--_accent);box-shadow:0 0 0 3px var(--_soft)}
  .dot.off{background:var(--_dim);box-shadow:none}
  a{color:var(--_accent-text);text-decoration:none}
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
      const vars = themeVars(this.getAttribute('theme')||'violet', this.getAttribute('accent'));
      const accent = outside.getPropertyValue('--mc-accent').trim() || vars['--mc-accent'];
      for(const k of VAR_NAMES){
        if(outside.getPropertyValue(k).trim()) continue;
        this.style.setProperty(k, k === '--mc-accent-soft' ? softOf(accent)
          : k === '--mc-accent-text' ? readableOn(accent) : vars[k]);
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
