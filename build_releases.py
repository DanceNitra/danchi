#!/usr/bin/env python3
"""Build /releases/ from data/catalog.json (iTunes lookup dump).

  python build_releases.py            # regenerates releases/, releases/index.html, sitemap.xml

Refresh the catalogue after each Friday release:
  https://itunes.apple.com/lookup?id=1554274941&entity=song&limit=200  ->  data/catalog.json
index.html is never touched.
"""
import json, os, re, html, datetime, shutil

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
songs = [x for x in cat["results"] if x.get("kind") == "song"]
songs.sort(key=lambda x: x["releaseDate"], reverse=True)
for i, s in enumerate(songs):
    s["slug"] = slug(s["trackName"]); s["date"] = s["releaseDate"][:10]
    s["idx"] = len(songs) - i  # 1 = first ever release
assert len({s["slug"] for s in songs}) == len(songs), "duplicate slugs"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,300..900&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root{--bg:#0A0E16;--panel:#14171F;--ink:#ECE9E2;--dim:#c9ccd6;--mute:#7c808c;--amber:#FFB454;--line:#1e2230}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:'Archivo',sans-serif;font-variation-settings:'wdth' 100;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:var(--amber)}.mono{font-family:'IBM Plex Mono',monospace}
.wrap{max-width:1100px;margin:0 auto;padding:0 24px}
header.top{border-bottom:1px solid var(--line)}header.top .wrap{display:flex;justify-content:space-between;align-items:center;height:60px}
header.top a{color:var(--ink);text-decoration:none;font-weight:700;letter-spacing:.14em;font-variation-settings:'wdth' 75}
header.top nav a{font-weight:400;letter-spacing:0;margin-left:22px;color:var(--dim);font-size:14px;font-variation-settings:'wdth' 100}
.rel{display:grid;grid-template-columns:minmax(280px,480px) 1fr;gap:48px;padding:56px 0;align-items:start}
@media(max-width:800px){.rel{grid-template-columns:1fr}}
.cover{width:100%;aspect-ratio:1;display:block;border:1px solid var(--line);box-shadow:0 30px 80px rgba(0,0,0,.6),0 0 0 1px rgba(255,180,84,.08)}
.k{font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--mute);letter-spacing:.06em}
h1{font-size:clamp(40px,6vw,72px);line-height:.95;margin:6px 0 18px;font-weight:800;font-variation-settings:'wdth' 68;letter-spacing:-.01em}
.meta{display:grid;grid-template-columns:auto 1fr;gap:6px 18px;font-size:15px;color:var(--dim);margin:22px 0}
.meta b{font-weight:500;color:var(--mute);font-family:'IBM Plex Mono',monospace;font-size:12px;padding-top:3px}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin:26px 0}
.btn{display:inline-block;padding:12px 18px;border:1px solid var(--line);color:var(--ink);text-decoration:none;font-size:15px;background:var(--panel)}
.btn:hover{border-color:var(--amber)}.btn.p{background:var(--amber);color:#0A0E16;border-color:var(--amber);font-weight:700}
audio{width:100%;margin-top:6px;filter:invert(1) hue-rotate(180deg) saturate(.6)}
.note{border-left:3px solid var(--amber);padding:2px 0 2px 18px;color:var(--dim);max-width:60ch;margin:24px 0}
.pn{display:flex;justify-content:space-between;gap:20px;border-top:1px solid var(--line);padding:22px 0 56px;font-size:15px}
.pn a{text-decoration:none;color:var(--dim)}.pn a:hover{color:var(--amber)}.pn span{display:block;color:var(--mute);font-size:12px;font-family:'IBM Plex Mono',monospace}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:22px;padding:8px 0 64px}
.card{text-decoration:none;color:var(--ink)}.card img{width:100%;aspect-ratio:1;display:block;border:1px solid var(--line)}
.card:hover img{outline:1px solid var(--amber)}.card b{display:block;margin-top:10px;font-weight:600;font-size:15px}.card small{color:var(--mute);font-family:'IBM Plex Mono',monospace;font-size:12px}
.year{margin:42px 0 12px;font-family:'IBM Plex Mono',monospace;color:var(--amber);font-size:13px;letter-spacing:.1em;border-bottom:1px solid var(--line);padding-bottom:8px}
h2{font-size:clamp(34px,5vw,56px);font-weight:800;font-variation-settings:'wdth' 68;margin:56px 0 8px;line-height:1}
.lede{color:var(--dim);max-width:62ch;margin:0 0 8px}
footer{border-top:1px solid var(--line);padding:28px 0 60px;color:var(--mute);font-size:13px}footer a{color:var(--dim);text-decoration:none;margin-right:18px}
"""

def head(title, desc, url, image, ld):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="music.song"><meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="1200"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{SITE}/apple-touch-icon.png"><link rel="apple-touch-icon" href="{SITE}/apple-touch-icon.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}</style></head><body>
<header class="top"><div class="wrap"><a href="{SITE}/">DANCHI</a><nav><a href="{SITE}/releases/">Releases</a><a href="{ARTIST['spotify']}">Spotify</a><a href="{ARTIST['apple']}">Apple Music</a><a href="{ARTIST['youtube']}">YouTube</a></nav></div></header>"""

FOOT = f"""<footer><div class="wrap"><a href="{SITE}/">danchi</a><a href="{ARTIST['instagram']}">Instagram</a><a href="{ARTIST['tiktok']}">TikTok</a><span>Nitra, Slovakia · new music every Friday</span></div></footer></body></html>"""

group = {"@type": "MusicGroup", "@id": SITE + "/#artist", "name": "DANCHI", "url": SITE + "/", "foundingLocation": {"@type": "Place", "name": ARTIST["from"]},
         "sameAs": [ARTIST["spotify"], ARTIST["apple"], ARTIST["youtube"], ARTIST["instagram"], ARTIST["tiktok"]]}

out_root = os.path.join(ROOT, "releases")
shutil.rmtree(out_root, ignore_errors=True); os.makedirs(out_root)
urls = []
for i, s in enumerate(songs):
    prev_ = songs[i + 1] if i + 1 < len(songs) else None   # older
    next_ = songs[i - 1] if i > 0 else None                 # newer
    url = f"{SITE}/releases/{s['slug']}/"; img = art(s["artworkUrl100"], 1200)
    title = f"{s['trackName']} — DANCHI"
    desc = f"{s['trackName']} by DANCHI, single released {pretty_date(s['date'])}. {dur(s['trackTimeMillis'])}, {s['primaryGenreName'].lower()}. Listen on Apple Music, Spotify and YouTube."
    ld = {"@context": "https://schema.org", "@graph": [group,
        {"@type": "MusicRecording", "@id": url + "#recording", "name": s["trackName"], "url": url, "image": img, "duration": iso_dur(s["trackTimeMillis"]), "datePublished": s["date"], "genre": s["primaryGenreName"],
         "byArtist": {"@id": SITE + "/#artist"}, "inAlbum": {"@type": "MusicAlbum", "name": s["collectionName"], "albumReleaseType": "SingleRelease", "byArtist": {"@id": SITE + "/#artist"}, "datePublished": s["date"], "url": s["collectionViewUrl"].split("?")[0]},
         "sameAs": [s["trackViewUrl"].split("?")[0]], "audio": {"@type": "AudioObject", "contentUrl": s["previewUrl"], "encodingFormat": "audio/aac", "duration": "PT30S"}},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "DANCHI", "item": SITE + "/"}, {"@type": "ListItem", "position": 2, "name": "Releases", "item": SITE + "/releases/"}, {"@type": "ListItem", "position": 3, "name": s["trackName"], "item": url}]}]}
    note = NOTES.get(s["slug"])
    body = f"""<main class="wrap"><div class="rel">
<img class="cover" src="{img}" width="1200" height="1200" alt="{html.escape(s['trackName'])} — DANCHI single cover" loading="eager">
<div><div class="k">RELEASE {s['idx']:02d} OF {len(songs)} · SINGLE</div><h1>{html.escape(s['trackName'])}</h1>
<div class="meta"><b>ARTIST</b><span>DANCHI · {ARTIST['from']}</span><b>RELEASED</b><span>{pretty_date(s['date'])}</span><b>LENGTH</b><span>{dur(s['trackTimeMillis'])}</span><b>GENRE</b><span>{html.escape(s['primaryGenreName'])}</span></div>
<div class="k">30-SECOND PREVIEW</div><audio controls preload="none" src="{s['previewUrl']}"></audio>
<div class="btns"><a class="btn p" href="{ARTIST['spotify']}">Spotify</a><a class="btn" href="{s['trackViewUrl'].split('?')[0]}">Apple Music</a><a class="btn" href="{ARTIST['youtube']}">YouTube</a></div>
{f'<div class="note">{html.escape(note)}</div>' if note else ''}
</div></div>
<div class="pn"><div>{f'<a href="{SITE}/releases/{prev_["slug"]}/"><span>OLDER</span>← {html.escape(prev_["trackName"])}</a>' if prev_ else ''}</div><div style="text-align:right">{f'<a href="{SITE}/releases/{next_["slug"]}/"><span>NEWER</span>{html.escape(next_["trackName"])} →</a>' if next_ else ''}</div></div></main>"""
    d = os.path.join(out_root, s["slug"]); os.makedirs(d)
    open(os.path.join(d, "index.html"), "w").write(head(title, desc, url, img, ld) + body + FOOT)
    urls.append((url, s["date"]))

# index
by_year = {}
for s in songs: by_year.setdefault(s["date"][:4], []).append(s)
idx_url = SITE + "/releases/"
ld = {"@context": "https://schema.org", "@graph": [group, {"@type": "ItemList", "name": "DANCHI releases", "url": idx_url, "numberOfItems": len(songs),
      "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}/releases/{s['slug']}/", "name": s["trackName"]} for i, s in enumerate(songs)]}]}
cards = ""
for y in sorted(by_year, reverse=True):
    cards += f'<div class="year">{y} · {len(by_year[y])} RELEASES</div><div class="grid">'
    for s in by_year[y]:
        cards += f'<a class="card" href="{SITE}/releases/{s["slug"]}/"><img src="{art(s["artworkUrl100"],600)}" width="600" height="600" loading="lazy" alt="{html.escape(s["trackName"])} cover"><b>{html.escape(s["trackName"])}</b><small>{pretty_date(s["date"])}</small></a>'
    cards += "</div>"
first, last = songs[-1]["date"][:4], songs[0]["date"][:4]
body = f"""<main class="wrap"><h2>Releases</h2><p class="lede">{len(songs)} singles by DANCHI, {first}–{last}, from {ARTIST['from']}. Every release has its own page with a 30-second preview and links to Apple Music, Spotify and YouTube.</p>{cards}</main>"""
open(os.path.join(out_root, "index.html"), "w").write(head("Releases — DANCHI", f"All {len(songs)} DANCHI singles, {first}–{last}, with previews and streaming links.", idx_url, art(songs[0]["artworkUrl100"], 1200), ld) + body + FOOT)

# sitemap (root stays first)
today = datetime.date.today().isoformat()
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      f"<url><loc>{SITE}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>",
      f"<url><loc>{idx_url}</loc><lastmod>{songs[0]['date']}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>"]
sm += [f"<url><loc>{u}</loc><lastmod>{d}</lastmod><priority>0.7</priority></url>" for u, d in urls]
sm.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
print(f"built {len(songs)} release pages + index + sitemap")
