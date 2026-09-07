#!/usr/bin/env python3
"""Build /releases/ from data/catalog.json (iTunes lookup dump).

  python build_releases.py            # regenerates releases/, releases/index.html, sitemap.xml

Refresh the catalogue after each Friday release:
  https://itunes.apple.com/lookup?id=1554274941&entity=song&limit=200  ->  data/catalog.json
index.html is never touched.
"""
import json, os, re, html, datetime, shutil, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://dancenitra.github.io/danchi"
ARTIST = {
    "name": "DANCHI", "id": 1554274941,
    "spotify": "https://open.spotify.com/artist/5FKtxmBPtW1OxBxa3AdkXo",
    "apple": "https://music.apple.com/artist/danchi/1554274941",
    "youtube": "https://www.youtube.com/channel/UCn19TQbANA8838DYnylaQCg",
    "instagram": "https://www.instagram.com/danchinitra/",
    "tiktok": "https://www.tiktok.com/@danchinitra",
    "from": "Nitra, Slovakia",
}
# the only per-track text that is the artist's own words (Apple Music bio)
NOTES = {
    "cesta-domov": "Cesta Domov means “the way home” in Slovak. It is the only title in the catalogue in my own language and the track that sounds most like where I’m from: concrete blocks, late evenings, one light still on. It is the closest thing I have to a signature.",
}

def slug(s):
    s = re.sub(r"[’'\"]", "", s.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

def art(url, px):  # Apple CDN serves any size; keep repo image-free
    return re.sub(r"/\d+x\d+bb\.jpg$", f"/{px}x{px}bb.jpg", url)

def dur(ms):
    s = ms // 1000
    return f"{s//60}:{s%60:02d}"

def iso_dur(ms):
    s = ms // 1000
    return f"PT{s//60}M{s%60}S"

def pretty_date(d):
    return datetime.date.fromisoformat(d).strftime("%-d %B %Y")

cat = json.load(open(os.path.join(ROOT, "data", "catalog.json")))
# optional exact links, filled in over time: {"cesta-domov": {"spotify": "https://open.spotify.com/track/...", "youtube": "https://youtu.be/..."}}
LINKS_PATH = os.path.join(ROOT, "data", "links.json")
LINKS = json.load(open(LINKS_PATH)) if os.path.exists(LINKS_PATH) else {}
songs = [x for x in cat["results"] if x.get("kind") == "song"]
songs.sort(key=lambda x: x["releaseDate"], reverse=True)
for i, s in enumerate(songs):
    s["slug"] = slug(s["trackName"]); s["date"] = s["releaseDate"][:10]
    s["idx"] = len(songs) - i  # 1 = first ever release
assert len({s["slug"] for s in songs}) == len(songs), "duplicate slugs"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..900&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root{--dusk:#14171F;--panel:#1C2029;--line:#2B303C;--amber:#FFB454;--fog:#9BA0AD;--ink:#ECE9E2}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--dusk);color:var(--ink);font-family:'Archivo',sans-serif;line-height:1.5;min-height:100vh;overflow-x:hidden;-webkit-font-smoothing:antialiased}
a{color:var(--ink)}
/* facade: every cover is a window; the current release is the one light still on */
.facade{position:fixed;inset:0;z-index:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:2px;align-content:start;padding:2px;overflow:hidden}
.facade img{width:100%;height:auto;aspect-ratio:1;display:block;object-fit:cover;opacity:.16;filter:saturate(.5)}
.facade img.lit{opacity:.85;filter:none;box-shadow:0 0 18px 6px rgba(255,180,84,.45),0 0 60px 20px rgba(255,180,84,.18);position:relative;z-index:1}
.facade img.near{opacity:.30}
.veil{position:fixed;inset:0;z-index:1;pointer-events:none;background:rgba(20,23,31,.46)}
.page{position:relative;z-index:2;max-width:980px;margin:0 auto;padding:36px 22px 40px}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:44px}
.brand{font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.28em;text-transform:uppercase;color:var(--amber);text-decoration:none}
.top nav a{font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--fog);text-decoration:none;margin-left:20px}
.top nav a:hover{color:var(--ink)}
@media(max-width:760px){.top{margin-bottom:28px}.top nav a{margin-left:14px}.top nav a.x{display:none}.page{padding:22px 16px 32px}.count{line-height:1.9}}
.eyebrow{font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.28em;text-transform:uppercase;color:var(--amber);margin:0 0 14px}
h1{font-variation-settings:'wdth' 122;font-weight:900;font-size:clamp(40px,9vw,76px);line-height:.9;text-transform:uppercase;margin:0;text-shadow:0 2px 14px rgba(13,15,22,.85)}
.count{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.2em;color:var(--fog);margin-top:12px;text-transform:uppercase}.count b{color:var(--amber);font-weight:500}
.rel{display:grid;grid-template-columns:minmax(240px,400px) 1fr;gap:40px;align-items:start;margin-top:36px}
@media(max-width:760px){.rel{grid-template-columns:1fr}}
.cover{width:100%;height:auto;aspect-ratio:1;object-fit:cover;display:block;border:1px solid var(--line);box-shadow:0 30px 80px rgba(13,15,22,.85),0 0 40px rgba(255,180,84,.12)}
.tagline{font-size:15.5px;font-weight:300;color:#c9ccd6;max-width:36ch;text-shadow:0 1px 8px rgba(13,15,22,.9);margin:0 0 6px}
.tagline em{font-style:normal;color:var(--ink)}
.links{margin-top:22px;display:grid;gap:10px}
.win{position:relative;display:flex;align-items:center;justify-content:space-between;gap:14px;padding:17px 18px 17px 20px;background:rgba(24,28,37,.62);border:1px solid var(--line);text-decoration:none;color:var(--ink);transition:background .25s,border-color .25s,transform .15s;backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);text-shadow:0 1px 6px rgba(13,15,22,.8)}
.win::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--line);transition:background .25s,box-shadow .25s}
.win:hover,.win:focus-visible{background:rgba(35,40,55,.88);border-color:#3A4152;transform:translateX(2px);outline:none}
.win:hover::before{background:var(--amber);box-shadow:0 0 12px rgba(255,180,84,.6)}
.w-name{font-weight:600;font-size:16px}.w-hint{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--fog)}
.player{margin-top:22px;background:rgba(24,28,37,.62);border:1px solid var(--line);padding:14px 18px;backdrop-filter:blur(4px)}
.player .w-hint{display:block;margin-bottom:8px}
audio{width:100%;height:34px;filter:invert(1) hue-rotate(180deg) saturate(.5) brightness(.9)}
.note{border-left:3px solid var(--amber);padding:2px 0 2px 18px;color:#c9ccd6;font-weight:300;max-width:52ch;margin:24px 0 0;text-shadow:0 1px 8px rgba(13,15,22,.9)}
.pn{display:flex;justify-content:space-between;gap:20px;margin-top:44px}
.pn a{flex:1;max-width:48%}
@media(max-width:760px){.pn{flex-direction:column}.pn a{max-width:none}}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:14px}
.card{text-decoration:none;color:var(--ink);background:rgba(24,28,37,.62);border:1px solid var(--line);padding:8px;transition:border-color .25s,transform .15s;backdrop-filter:blur(4px)}
.card:hover{border-color:var(--amber);transform:translateY(-2px)}
.card img{width:100%;height:auto;aspect-ratio:1;object-fit:cover;display:block}.card b{display:block;margin-top:9px;font-weight:600;font-size:14px}.card small{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.14em;color:var(--fog);text-transform:uppercase}
.year{margin:34px 0 0;font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:.28em;text-transform:uppercase;color:var(--amber)}
footer{margin-top:52px;display:flex;justify-content:space-between;font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#7c8090}
footer .dot{color:var(--amber)}footer a{color:#7c8090;text-decoration:none}
"""

def head(title, desc, url, image, ld, facade):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="music.song"><meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="1200"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{SITE}/apple-touch-icon.png"><link rel="apple-touch-icon" href="{SITE}/apple-touch-icon.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}</style></head><body>
<div class="facade" aria-hidden="true">{facade}</div><div class="veil"></div>
<div class="page"><div class="top"><a class="brand" href="{SITE}/">Danchi</a><nav><a href="{SITE}/releases/">Releases</a><a class="x" href="{ARTIST['spotify']}">Spotify</a><a class="x" href="{ARTIST['apple']}">Apple Music</a><a class="x" href="{ARTIST['youtube']}">YouTube</a></nav></div>"""

FOOT = f"""<footer><span><a href="{SITE}/">Danchi</a> · <a href="{ARTIST['instagram']}">Instagram</a> · <a href="{ARTIST['tiktok']}">TikTok</a></span><span><span class="dot">&#9679;</span>&nbsp;the light is still on</span></footer></div></body></html>"""

group = {"@type": "MusicGroup", "@id": SITE + "/#artist", "name": "DANCHI", "url": SITE + "/", "foundingLocation": {"@type": "Place", "name": ARTIST["from"]},
         "sameAs": [ARTIST["spotify"], ARTIST["apple"], ARTIST["youtube"], ARTIST["instagram"], ARTIST["tiktok"]]}

import random
def facade_html(lit_slug=None):
    tiles = songs[:]; random.Random(7).shuffle(tiles); tiles = (tiles * 3)[:180]
    LIT = 58  # ~row 5, right of centre on a desktop grid: visible beside the cover, not under the title
    if lit_slug:
        j = next(i for i, t in enumerate(tiles) if t["slug"] == lit_slug)
        tiles[LIT], tiles[j] = tiles[j], tiles[LIT]
    out = []
    for i, t in enumerate(tiles):
        cls = ' class="lit"' if (lit_slug and i == LIT) else ""
        out.append(f'<img src="{art(t["artworkUrl100"],100)}" alt="" loading="lazy" decoding="async"{cls}>')
    return "".join(out)

out_root = os.path.join(ROOT, "releases")
shutil.rmtree(out_root, ignore_errors=True); os.makedirs(out_root)
urls = []
for i, s in enumerate(songs):
    prev_ = songs[i + 1] if i + 1 < len(songs) else None   # older
    next_ = songs[i - 1] if i > 0 else None                 # newer
    url = f"{SITE}/releases/{s['slug']}/"; img = art(s["artworkUrl100"], 1200)
    q = urllib.parse.quote(f"DANCHI {s['trackName']}")
    ex = LINKS.get(s["slug"], {})
    sp = ex.get("spotify") or f"https://open.spotify.com/search/{q}/tracks"
    yt = ex.get("youtube") or f"{ARTIST['youtube']}/search?query={q}"
    sp_hint = "Play this track" if ex.get("spotify") else "Find this track"
    yt_hint = "Watch this track" if ex.get("youtube") else "Find this track"
    title = f"{s['trackName']} — DANCHI"
    desc = f"{s['trackName']} by DANCHI, single released {pretty_date(s['date'])}. {dur(s['trackTimeMillis'])}, {s['primaryGenreName'].lower()}. Listen on Apple Music, Spotify and YouTube."
    ld = {"@context": "https://schema.org", "@graph": [group,
        {"@type": "MusicRecording", "@id": url + "#recording", "name": s["trackName"], "url": url, "image": img, "duration": iso_dur(s["trackTimeMillis"]), "datePublished": s["date"], "genre": s["primaryGenreName"],
         "byArtist": {"@id": SITE + "/#artist"}, "inAlbum": {"@type": "MusicAlbum", "name": s["collectionName"], "albumReleaseType": "SingleRelease", "byArtist": {"@id": SITE + "/#artist"}, "datePublished": s["date"], "url": s["collectionViewUrl"].split("?")[0]},
         "sameAs": [s["trackViewUrl"].split("?")[0]], "audio": {"@type": "AudioObject", "contentUrl": s["previewUrl"], "encodingFormat": "audio/aac", "duration": "PT30S"}},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "DANCHI", "item": SITE + "/"}, {"@type": "ListItem", "position": 2, "name": "Releases", "item": SITE + "/releases/"}, {"@type": "ListItem", "position": 3, "name": s["trackName"], "item": url}]}]}
    note = NOTES.get(s["slug"])
    body = f"""<p class="eyebrow">Nitra · Slovakia · Single</p><h1>{html.escape(s['trackName'])}</h1>
<div class="count">Release <b>{s['idx']:02d}</b> of {len(songs)} · {pretty_date(s['date'])} · {dur(s['trackTimeMillis'])} · {html.escape(s['primaryGenreName'])}</div>
<div class="rel"><img class="cover" src="{img}" width="1200" height="1200" alt="{html.escape(s['trackName'])} — DANCHI single cover">
<div>
<div class="player"><span class="w-hint">Tap to hear · 30 s</span><audio controls preload="none" src="{s['previewUrl']}"></audio></div>
<div class="links"><a class="win" href="{s["trackViewUrl"].split("&")[0]}"><span class="w-name">Apple Music</span><span class="w-hint">Play this track</span></a><a class="win" href="{sp}"><span class="w-name">Spotify</span><span class="w-hint">{sp_hint}</span></a><a class="win" href="{yt}"><span class="w-name">YouTube</span><span class="w-hint">{yt_hint}</span></a><a class="win" href="https://song.link/i/{s['trackId']}"><span class="w-name">Everywhere else</span><span class="w-hint">Deezer, Tidal, Amazon &#8230;</span></a></div>
{f'<div class="note">{html.escape(note)}</div>' if note else ''}
</div></div>
<div class="pn">{f'<a class="win" href="{SITE}/releases/{prev_["slug"]}/"><span class="w-name">{html.escape(prev_["trackName"])}</span><span class="w-hint">Older</span></a>' if prev_ else '<span></span>'}{f'<a class="win" href="{SITE}/releases/{next_["slug"]}/"><span class="w-name">{html.escape(next_["trackName"])}</span><span class="w-hint">Newer</span></a>' if next_ else '<span></span>'}</div>"""
    d = os.path.join(out_root, s["slug"]); os.makedirs(d)
    open(os.path.join(d, "index.html"), "w").write(head(title, desc, url, img, ld, facade_html(s["slug"])) + body + FOOT)
    urls.append((url, s["date"]))

# index
by_year = {}
for s in songs: by_year.setdefault(s["date"][:4], []).append(s)
idx_url = SITE + "/releases/"
ld = {"@context": "https://schema.org", "@graph": [group, {"@type": "ItemList", "name": "DANCHI releases", "url": idx_url, "numberOfItems": len(songs),
      "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}/releases/{s['slug']}/", "name": s["trackName"]} for i, s in enumerate(songs)]}]}
cards = ""
for y in sorted(by_year, reverse=True):
    cards += f'<div class="year">{y} · {len(by_year[y])} releases</div><div class="grid">'
    for s in by_year[y]:
        cards += f'<a class="card" href="{SITE}/releases/{s["slug"]}/"><img src="{art(s["artworkUrl100"],400)}" width="400" height="400" loading="lazy" alt="{html.escape(s["trackName"])} cover"><b>{html.escape(s["trackName"])}</b><small>{pretty_date(s["date"])}</small></a>'
    cards += "</div>"
first, last = songs[-1]["date"][:4], songs[0]["date"][:4]
body = f"""<p class="eyebrow">Nitra · Slovakia</p><h1>Releases</h1><div class="count"><b>{len(songs)}</b> singles · {first}–{last} · new music every Friday</div>{cards}"""
open(os.path.join(out_root, "index.html"), "w").write(head("Releases — DANCHI", f"All {len(songs)} DANCHI singles, {first}–{last}, each with a 30-second preview and Apple Music, Spotify and YouTube links.", idx_url, art(songs[0]["artworkUrl100"], 1200), ld, facade_html()) + body + FOOT)

# sitemap (root stays first)
today = datetime.date.today().isoformat()
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      f"<url><loc>{SITE}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>",
      f"<url><loc>{idx_url}</loc><lastmod>{songs[0]['date']}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>"]
sm += [f"<url><loc>{u}</loc><lastmod>{d}</lastmod><priority>0.7</priority></url>" for u, d in urls]
sm.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
# keep index.html's Releases button count in sync (only that number)
idx = os.path.join(ROOT, "index.html")
if os.path.exists(idx):
    h = open(idx).read()
    h2 = re.sub(r'(<a class="win releases" href="releases/"><span class="w-name"><b>)\d+(</b>)', r"\g<1>%d\g<2>" % len(songs), h)
    if h2 != h: open(idx, "w").write(h2); print("index.html: release count updated")

print(f"built {len(songs)} release pages + index + sitemap")
