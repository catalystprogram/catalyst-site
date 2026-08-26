"""Build index.html = index-base.html + the Projects section.

index-base.html is the hand-edited source; index.html is generated.
Cards link through to the full listing at mentors.html#<slug>.
"""
import json, re, html

PREVIEW = 6          # projects shown on the home page
src = open('index-base.html', encoding='utf-8').read()
mentors = json.load(open('mentors.json', encoding='utf-8'))

# flatten to projects, then take one per mentor so the preview shows variety
flat = []
for m in mentors:
    multi = len(m['projects']) > 1
    for i, p in enumerate(m['projects']):
        flat.append({
            'slug': m['slug'] + (f'-{i + 1}' if multi else ''),
            'mentor': m['slug'], 'name': m['name'], 'org': m['org'],
            'photo': m['photo'], 'initials': m['initials'],
            'title': p['title'], 'summary': p['summary'],
        })
# one per mentor first (variety), then backfill remaining slots with the rest
seen, picks = set(), []
for c in flat:
    if c['mentor'] not in seen and len(picks) < PREVIEW:
        seen.add(c['mentor'])
        picks.append(c)
for c in flat:
    if len(picks) >= PREVIEW:
        break
    if c not in picks:
        picks.append(c)
picks.sort(key=flat.index)

e = html.escape
cards = "\n".join(f"""          <article class="pcard">
            <a class="pcard__link" href="mentors.html#{c['slug']}" aria-label="{e(c['title'])}"></a>
            <div class="pcard__top">
              {'<img class="pcard__avatar" src="%s" alt="" loading="lazy" width="480" height="480" />' % c['photo']
                if c['photo'] else '<div class="pcard__avatar">%s</div>' % e(c['initials'])}
              <div>
                <div class="pcard__name">{e(c['name'])}</div>
                <div class="pcard__org">{e(c['org'])}</div>
              </div>
            </div>
            <div>
              <div class="pcard__title">{e(c['title'])}</div>
              <div class="pcard__sum">{e(c['summary'])}</div>
            </div>
          </article>""" for c in picks)

SECTION = f"""    <section class="section" id="projects">
      <div class="container">
        <div class="section__header">
          <h2 class="section__title">Projects this term</h2>
          <p class="section__desc">
            <a class="plink" href="https://forms.fillout.com/t/5hBi1ayhj8us" target="_blank" rel="noopener noreferrer">Apply here</a>
            to be a student mentee on one of these projects. Applications are due
            September&nbsp;14th, AoE.
          </p>
        </div>
        <div class="pgrid">
{cards}
        </div>
        <!-- hidden for now; restore when the full listing goes live:
        <a class="pall" href="mentors.html">{'See all %d projects' % len(flat) if len(picks) < len(flat) else 'Browse all projects'}</a>
        -->
      </div>
    </section>

"""

CSS = """
    /* --- Projects preview (prototype) --- */
    .pgrid {
      display: grid; column-gap: 46px; row-gap: 34px;
      grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
    }
    .pcard {
      position: relative; border-top: 1px solid var(--line); padding-top: 20px;
      display: flex; flex-direction: column; gap: 14px;
    }
    .pcard__link { position: absolute; inset: -6px -10px; z-index: 0; }
    .pcard__link:focus-visible { outline: 2px solid var(--teal); outline-offset: 0; }
    .pcard > *:not(.pcard__link) { position: relative; z-index: 1; pointer-events: none; }
    .pcard__top { display: flex; gap: 13px; align-items: center; }
    .pcard__avatar {
      width: 54px; height: 54px; border-radius: 50%; flex: none; object-fit: cover;
      background: rgba(224,238,235,.08); border: 1px solid rgba(224,238,235,.16);
      display: grid; place-items: center; font-weight: 700; font-size: 18px; color: var(--text-dim);
    }
    .pcard__name { font-size: 15.5px; font-weight: 600; letter-spacing: -0.01em; line-height: 1.25; }
    .pcard__org { color: var(--text-dim); font-size: 13px; margin-top: 3px; }
    .pcard__title {
      font-size: 17px; font-weight: 700; letter-spacing: -0.015em; line-height: 1.32;
      transition: color .2s ease;
    }
    .pcard__title::after {
      content: '\\203A'; display: inline-block; margin-left: 8px;
      color: var(--teal); font-weight: 500;
    }
    .pcard:hover .pcard__title { color: #fff; }
    .pcard__sum {
      font-size: 14px; color: var(--text-dim); line-height: 1.5; margin-top: 8px;
      display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
    }
    .section__desc .plink { color: var(--teal); font-weight: 600; }
    .section__desc .plink:hover { text-decoration: underline; }
    .pall {
      display: inline-block; margin-top: 44px;
      font-size: 15px; font-weight: 600; color: var(--teal);
    }
    .pall::after { content: '\\203A'; margin-left: 8px; display: inline-block; }
"""

out = src
# 1. styles, appended just before the closing </style>
out = out.replace('  </style>', CSS + '  </style>', 1)
# 2. section, inserted immediately after the hero (first section on the page)
anchor = '    <section class="section section--about" id="about">'
assert 'id="projects"' not in src, 'template already has a Projects section'
assert out.count(anchor) == 1
out = out.replace(anchor, SECTION + anchor, 1)
# 3. nav + footer entries
out = out.replace('<li><a href="#about" class="nav__link">About</a></li>',
                  '<li><a href="#projects" class="nav__link">Projects</a></li>\n'
                  '          <li><a href="#about" class="nav__link">About</a></li>', 1)
out = out.replace('<li><a href="#about">About</a></li>',
                  '<li><a href="#projects">Projects</a></li>\n'
                  '            <li><a href="#about">About</a></li>', 1)

open('index.html', 'w', encoding='utf-8').write(out)
print(f'index.html written: {len(out)} bytes | {len(picks)} preview cards of {len(flat)} projects')
