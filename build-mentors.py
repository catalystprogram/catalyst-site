"""Generate mentors.html (prototype) from mentors.json + chunks reused from index.html.

Browse unit is the PROJECT: one card per project, so a mentor with N projects
appears N times (the SPAR model). No cause-area tags or filters.
"""
import json, re, html

src = open('index-base.html', encoding='utf-8').read()
css = src[src.index('<style>') + 7: src.index('</style>')]

BG_CSS = css[css.index('/* ============================================================\n       PARTICLE FIELD BACKGROUND'):
             css.index('/* ============================================================\n       CONTENT OVERLAY')]
FONT_FACE = css[css.index('@font-face'): css.index('*, *::before')]
TOKENS = css[css.index(':root {'): css.index('/* ============================================================\n       PARTICLE FIELD BACKGROUND')]
NAV_CSS = css[css.index('/* --- Nav --- */'): css.index('/* --- Buttons / links --- */')]
NAV_HTML = src[src.index('    <nav class="nav">'): src.index('</nav>') + 6]
# this page has none of the home page's anchors, so point them back at it
NAV_HTML = re.sub(r'href="#(?!top)', 'href="index.html#', NAV_HTML)
NAV_HTML = NAV_HTML.replace('href="#top"', 'href="index.html"')
PARTICLES = src[src.index('  <!-- ===== Particle field script'):
                src.index('</script>', src.index('requestAnimationFrame(animate)', src.index('  <!-- ===== Particle field script'))) + 9]
NAVSOLID = src[src.index('  <!-- ===== Solidify nav'): src.index('</script>', src.index('  <!-- ===== Solidify nav')) + 9]
NAVSOLID = NAVSOLID.replace("document.querySelector('.hero__title')",
                            "document.querySelector('.hero__title, .page-head h1')")


# ---------- tiny markdown renderer ----------
def md(text):
    if not text:
        return ""
    text = re.sub(r'\+\+|\*{4,}', '', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    out, buf, in_ul = [], [], False

    def inline(s):
        s = html.escape(s)
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                   r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', s)
        s = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', s)
        return s

    def flush():
        nonlocal buf
        if buf:
            out.append('<p>' + inline(' '.join(buf)) + '</p>')
            buf = []

    for ln in text.split('\n'):
        s = ln.strip()
        if not s:
            flush()
            if in_ul:
                out.append('</ul>'); in_ul = False
            continue
        h = re.match(r'^(#{2,4})\s+(.*)', s)
        if h:
            flush()
            if in_ul:
                out.append('</ul>'); in_ul = False
            out.append(f'<h4>{inline(h.group(2))}</h4>')
            continue
        b = re.match(r'^[-*•·]\s+(.*)', s)
        n = re.match(r'^(\d+)[.)]\s+(.*)', s)
        if b or n:
            flush()
            if not in_ul:
                out.append('<ul>'); in_ul = True
            out.append(f'<li>{inline(b.group(1) if b else n.group(2))}</li>')
            continue
        buf.append(s)
    flush()
    if in_ul:
        out.append('</ul>')
    return '\n'.join(out)


def usable_bio(b):
    """A lone URL isn't a bio — one mentor pasted a spreadsheet link into the field."""
    return '' if not b or re.fullmatch(r'https?://\S+', b.strip()) else b


mentors = json.load(open('mentors.json', encoding='utf-8'))

# ---------- flatten: one CARD per project ----------
cards = []
for m in mentors:
    multi = len(m['projects']) > 1
    for i, p in enumerate(m['projects']):
        cards.append({
            'slug': m['slug'] + (f'-{i + 1}' if multi else ''),
            'mentor': m['slug'],
            'name': m['name'], 'org': m['org'], 'photo': m['photo'],
            'initials': m['initials'],
            'bio_html': md(usable_bio(m['bio'])),
            'title': p['title'], 'summary': p['summary'],
            'desc_html': md(p['description']), 'q_html': md(p['question']),
        })
# sibling projects by the same mentor (fills the gap SPAR leaves)
for c in cards:
    c['siblings'] = [{'slug': o['slug'], 'title': o['title']}
                     for o in cards if o['mentor'] == c['mentor'] and o['slug'] != c['slug']]

DATA = json.dumps(cards, ensure_ascii=False)

PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Mentors &amp; Projects — Catalyst Program</title>
  <link rel="icon" href="favicon.ico" sizes="any" />
  <link rel="preload" href="fonts/schibsted-grotesk.woff2" as="font" type="font/woff2" crossorigin />
  <style>
{FONT_FACE}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

{TOKENS}
    html {{ scroll-behavior: smooth; }}
    body {{
      background: var(--ink); color: var(--text);
      font-family: 'Schibsted Grotesk', system-ui, -apple-system, sans-serif;
      line-height: 1.6; -webkit-font-smoothing: antialiased;
    }}
    ::selection {{ background: rgba(45, 212, 191, 0.3); }}

{BG_CSS}
    .content {{ position: relative; z-index: 10; }}
    .container {{ width: min(1180px, 100% - 48px); margin-inline: auto; }}
    a {{ color: inherit; text-decoration: none; }}

{NAV_CSS}

    /* ---------- page header ---------- */
    .page-head {{ padding: 64px 0 40px; }}
    .page-head h1 {{
      font-size: clamp(34px, 5vw, 52px); font-weight: 800;
      letter-spacing: -0.03em; line-height: 1.05; margin-bottom: 16px;
    }}
    .page-head p {{ color: var(--text-dim); font-size: 18px; max-width: 60ch; }}

    /* ---------- controls ---------- */
    .controls {{
      display: flex; flex-wrap: wrap; gap: 14px; align-items: center;
      justify-content: space-between; padding-bottom: 22px;
      border-bottom: 1px solid var(--line); margin-bottom: 26px;
    }}
    .status {{ color: var(--text-dim); font-size: 14.5px; }}
    .search {{
      flex: 0 1 280px; padding: 9px 14px; border-radius: 8px;
      border: 1px solid var(--line); background: rgba(255,255,255,.04);
      color: var(--text); font: inherit; font-size: 14px;
    }}
    .search::placeholder {{ color: rgba(224,238,235,.4); }}
    .search:focus {{ outline: none; border-color: var(--teal); }}

    /* ---------- project grid ---------- */
    /* flat entries separated by rules — no card fill, border box or radius */
    .grid {{
      display: grid; column-gap: 46px; row-gap: 34px;
      grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
      padding-bottom: 80px;
    }}
    .card {{
      position: relative; text-align: left; color: inherit;
      border-top: 1px solid var(--line); padding-top: 20px;
      display: flex; flex-direction: column; gap: 14px;
      transition: border-color .2s ease;
    }}
    .card:hover .card__ptitle {{ color: #fff; }}
    .card__link {{ position: absolute; inset: -6px -10px; z-index: 0; }}
    .card__link:focus-visible {{ outline: 2px solid var(--teal); outline-offset: 0; }}
    .card > *:not(.card__link) {{ position: relative; z-index: 1; pointer-events: none; }}
    .card__top {{ display: flex; gap: 13px; align-items: center; }}
    .avatar {{
      width: 54px; height: 54px; border-radius: 50%; flex: none;
      object-fit: cover; background: rgba(224,238,235,.08);
      border: 1px solid rgba(224,238,235,.16);
      display: grid; place-items: center;
      font-weight: 700; font-size: 18px; color: var(--text-dim);
    }}
    .card__name {{ font-size: 15.5px; font-weight: 600; letter-spacing: -0.01em; line-height: 1.25; }}
    .card__org {{ color: var(--text-dim); font-size: 13px; margin-top: 3px; }}
    .card__ptitle {{
      font-size: 17px; font-weight: 700; letter-spacing: -0.015em; line-height: 1.32;
      transition: color .2s ease;
    }}
    /* persistent chevron: a clickable affordance attached to the headline
       rather than a repeated call-to-action line */
    .card__ptitle::after {{
      content: '›'; display: inline-block; margin-left: 8px;
      color: var(--teal); font-weight: 500;
    }}
    .card__psum {{
      font-size: 14px; color: var(--text-dim); line-height: 1.5; margin-top: 8px;
      display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
    }}
    .empty {{ color: var(--text-dim); padding: 30px 0 90px; }}

    /* ---------- modal ---------- */
    .backdrop {{
      position: fixed; inset: 0; z-index: 100; display: none;
      background: rgba(4,10,16,.72); backdrop-filter: blur(6px);
      padding: 4vh 20px; overflow-y: auto;
    }}
    .backdrop.open {{ display: block; }}
    .modal {{
      width: min(820px, 100%); margin: 0 auto;
      background: #0e2130; border: 1px solid rgba(224,238,235,.14);
      border-radius: 4px; overflow: hidden; animation: rise .22s ease;
    }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(14px); }} }}
    .modal__head {{
      display: flex; gap: 18px; align-items: flex-start;
      padding: 24px 30px; border-bottom: 1px solid var(--line);
      position: sticky; top: 0; background: #0e2130; z-index: 2;
    }}
    .modal__head .avatar {{ width: 62px; height: 62px; font-size: 21px; }}
    .modal__name {{ font-size: 19px; font-weight: 700; letter-spacing: -0.015em; line-height: 1.2; }}
    .modal__org {{ color: var(--text-dim); font-size: 14px; margin-top: 3px; }}
    mark {{ background: rgba(224,238,235,.2); color: var(--text); padding: 0 2px; }}
    .mnav {{ margin-left: auto; display: flex; gap: 7px; flex: none; }}
    .mnav button {{
      width: 36px; height: 36px; border-radius: 3px; cursor: pointer;
      border: 1px solid var(--line); background: transparent; color: var(--text-dim);
      display: grid; place-items: center; transition: color .2s, border-color .2s;
    }}
    .mnav button:hover:not(:disabled) {{ color: var(--text); border-color: rgba(224,238,235,.35); }}
    .mnav button:disabled {{ opacity: .3; cursor: default; }}
    .close {{ font-size: 20px; line-height: 1; }}
    .modal__body {{ padding: 28px 30px 34px; }}
    /* plain sentence-case headings, not uppercase letterspaced eyebrows */
    .modal__label {{
      font-size: 15px; font-weight: 700; letter-spacing: -0.01em;
      color: var(--text); margin-bottom: 10px;
    }}
    .modal__title {{
      font-size: clamp(22px, 3.2vw, 28px); font-weight: 800;
      letter-spacing: -0.025em; line-height: 1.15; margin-bottom: 12px;
    }}
    .modal__lead {{ color: var(--text); font-size: 16.5px; margin-bottom: 22px; }}
    .prose p {{ color: var(--text-dim); font-size: 15.5px; }}
    .prose p + p {{ margin-top: 11px; }}
    .prose h4 {{ font-size: 15.5px; font-weight: 700; color: var(--text); margin: 18px 0 8px; }}
    .prose ul {{ margin: 10px 0 10px 20px; }}
    .prose li {{ color: var(--text-dim); font-size: 15.5px; margin-bottom: 6px; }}
    .prose a {{ color: var(--teal); text-decoration: underline; }}
    /* indented rule instead of a tinted rounded callout */
    .qbox {{ margin-top: 26px; padding-left: 20px; border-left: 2px solid rgba(224,238,235,.28); }}
    .qbox p, .qbox li {{ font-size: 15px; }}
    .section {{ margin-top: 30px; padding-top: 26px; border-top: 1px solid var(--line); }}
    .more-list {{ display: flex; flex-direction: column; }}
    .more-list a {{
      color: var(--text); font-size: 15px; font-weight: 500;
      padding: 12px 0; border-top: 1px solid var(--line);
      transition: color .2s ease;
    }}
    .more-list a:first-child {{ border-top: 0; padding-top: 2px; }}
    .more-list a:hover {{ color: #fff; }}

    @media (max-width: 620px) {{
      .modal__head {{ padding: 18px 20px; gap: 13px; }}
      .modal__head .avatar {{ width: 50px; height: 50px; font-size: 17px; }}
      .modal__body {{ padding: 22px 20px 28px; }}
    }}
  </style>
</head>
<body>
  <div class="bg">
    <div class="bg__orb bg__orb--1"></div>
    <div class="bg__orb bg__orb--2"></div>
    <div class="bg__orb bg__orb--3"></div>
  </div>
  <canvas class="bg__canvas" id="particles"></canvas>
  <div class="count" id="count"></div>

  <div class="content">
{NAV_HTML}

    <header class="page-head">
      <div class="container">
        <h1>Mentors &amp; projects</h1>
        <p>Fall 2026 cohort. Browse the projects on offer this term — open one to read the full
          description, the mentor's background, and the question you'll answer when applying.</p>
      </div>
    </header>

    <main class="container">
      <div class="controls">
        <p class="status" id="status"></p>
        <input class="search" id="search" type="search" placeholder="Search projects or mentors…" aria-label="Search projects or mentors" />
      </div>
      <div class="grid" id="grid"></div>
      <p class="empty" id="empty" hidden></p>
    </main>
  </div>

  <div class="backdrop" id="backdrop" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
    <div class="modal" id="modal"></div>
  </div>

  <script id="project-data" type="application/json">{DATA}</script>
  <script>
  (() => {{
    const CARDS = JSON.parse(document.getElementById('project-data').textContent);
    const grid = document.getElementById('grid');
    const searchEl = document.getElementById('search');
    const emptyEl = document.getElementById('empty');
    const statusEl = document.getElementById('status');
    const backdrop = document.getElementById('backdrop');
    const modal = document.getElementById('modal');
    let query = '', view = [], current = -1;

    const esc = s => String(s).replace(/[&<>"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
    const hl = s => {{
      const e = esc(s);
      if (!query) return e;
      const rx = new RegExp('(' + query.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + ')', 'ig');
      return e.replace(rx, '<mark>$1</mark>');
    }};
    const avatar = c => c.photo
      ? `<img class="avatar" src="${{c.photo}}" alt="" loading="lazy" width="480" height="480">`
      : `<div class="avatar">${{esc(c.initials)}}</div>`;

    const matches = c => !query || (c.name + ' ' + c.org + ' ' + c.title + ' ' +
      c.summary + ' ' + c.desc_html).toLowerCase().includes(query);

    function render() {{
      view = CARDS.map((c, i) => i).filter(i => matches(CARDS[i]));
      statusEl.textContent = view.length === CARDS.length
        ? `Showing all ${{CARDS.length}} projects`
        : `Showing ${{view.length}} of ${{CARDS.length}} projects`;
      emptyEl.hidden = view.length > 0;
      emptyEl.textContent = `Nothing matches "${{query}}". Try fewer or shorter words.`;
      grid.innerHTML = view.map(i => {{
        const c = CARDS[i];
        return `
        <article class="card">
          <a class="card__link" href="#${{c.slug}}" data-i="${{i}}" aria-label="${{esc(c.title)}}"></a>
          <div class="card__top">
            ${{avatar(c)}}
            <div>
              <div class="card__name">${{hl(c.name)}}</div>
              <div class="card__org">${{hl(c.org)}}</div>
            </div>
          </div>
          <div>
            <div class="card__ptitle">${{hl(c.title)}}</div>
            ${{c.summary ? `<div class="card__psum">${{hl(c.summary)}}</div>` : ''}}
          </div>
        </article>`;
      }}).join('');
      grid.querySelectorAll('.card__link').forEach(a => a.onclick = e => {{
        e.preventDefault(); open(+a.dataset.i);
      }});
    }}

    function syncURL(push) {{
      const p = new URLSearchParams();
      if (query) p.set('q', query);
      const qs = p.toString();
      const url = location.pathname + (qs ? '?' + qs : '') +
                  (current >= 0 ? '#' + CARDS[current].slug : '');
      history[push ? 'pushState' : 'replaceState']({{}}, '', url);
    }}
    function readURL() {{
      const p = new URLSearchParams(location.search);
      query = (p.get('q') || '').toLowerCase();
      searchEl.value = p.get('q') || '';
      render();
      const i = CARDS.findIndex(c => c.slug === location.hash.slice(1));
      if (i >= 0) open(i, true); else close(true);
    }}

    function open(i, silent) {{
      const c = CARDS[i];
      current = i;
      const pos = view.indexOf(i);
      modal.innerHTML = `
        <div class="modal__head">
          ${{avatar(c)}}
          <div>
            <div class="modal__name">${{esc(c.name)}}</div>
            <div class="modal__org">${{esc(c.org)}}</div>
          </div>
          <div class="mnav">
            <button id="prevBtn" aria-label="Previous project" ${{pos <= 0 ? 'disabled' : ''}}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg></button>
            <button id="nextBtn" aria-label="Next project" ${{pos < 0 || pos >= view.length - 1 ? 'disabled' : ''}}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg></button>
            <button class="close" id="closeBtn" aria-label="Close">×</button>
          </div>
        </div>
        <div class="modal__body">
          <h2 class="modal__title" id="modalTitle">${{esc(c.title)}}</h2>
          ${{c.summary ? `<p class="modal__lead">${{esc(c.summary)}}</p>` : ''}}
          <div class="prose">${{c.desc_html}}</div>
          ${{c.q_html ? `<div class="qbox"><div class="modal__label">Application question</div><div class="prose">${{c.q_html}}</div></div>` : ''}}
          ${{c.siblings.length ? `
            <div class="section">
              <div class="modal__label">More from ${{esc(c.name)}}</div>
              <div class="more-list">
                ${{c.siblings.map(s => `<a href="#${{s.slug}}" data-slug="${{s.slug}}">${{esc(s.title)}}</a>`).join('')}}
              </div>
            </div>` : ''}}
          ${{c.bio_html ? `
            <div class="section">
              <div class="modal__label">About the mentor</div>
              <div class="prose">${{c.bio_html}}</div>
            </div>` : ''}}
        </div>`;
      backdrop.classList.add('open');
      backdrop.scrollTop = 0;
      document.body.style.overflow = 'hidden';
      modal.querySelector('#closeBtn').onclick = () => close();
      modal.querySelector('#prevBtn').onclick = () => step(-1);
      modal.querySelector('#nextBtn').onclick = () => step(1);
      modal.querySelectorAll('.more-list a').forEach(a => a.onclick = e => {{
        e.preventDefault();
        const j = CARDS.findIndex(x => x.slug === a.dataset.slug);
        if (j >= 0) open(j);
      }});
      modal.querySelector('#closeBtn').focus();
      if (!silent) syncURL(true);
    }}

    function step(d) {{
      const n = view[view.indexOf(current) + d];
      if (n !== undefined) open(n);
    }}
    function close(silent) {{
      backdrop.classList.remove('open');
      document.body.style.overflow = '';
      current = -1;
      if (!silent) syncURL(true);
    }}

    backdrop.onclick = e => {{ if (e.target === backdrop) close(); }};
    document.addEventListener('keydown', e => {{
      if (!backdrop.classList.contains('open')) return;
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowLeft') step(-1);
      else if (e.key === 'ArrowRight') step(1);
    }});
    let t;
    searchEl.oninput = e => {{
      clearTimeout(t);
      t = setTimeout(() => {{ query = e.target.value.trim().toLowerCase(); render(); syncURL(); }}, 200);
    }};
    window.addEventListener('popstate', readURL);
    readURL();
  }})();
  </script>

{NAVSOLID}
{PARTICLES}
</body>
</html>
"""
open('mentors.html', 'w', encoding='utf-8').write(PAGE)
print('mentors.html written:', len(PAGE), 'bytes |', len(cards), 'project cards from', len(mentors), 'mentors')
