import requests
from db import get_existing_news_links

URL = "https://thorn-iodize-crushing.ngrok-free.dev/cnbc/market"

def fetch_news():
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        response = r.json()
    except (requests.RequestException, ValueError) as e:
        print(f"Gagal mengambil berita: {e}")
        return []

    data = response.get("data", {}).get("posts", [])

    existing_links = get_existing_news_links()

    # Jika database gagal diperiksa, jangan proses berita
    if existing_links is None:
        print("Gagal memeriksa database. Proses dibatalkan.")
        return []

    news = []
    seen_links = set()

    for a in data:
        link = (a.get("link") or "").strip()

        if not link:
            continue

        # Hindari duplikat dalam respons API
        if link in seen_links:
            continue
        seen_links.add(link)

        # Lewati berita yang sudah tersimpan
        if link in existing_links:
            continue

        news.append({
            "judul": a.get("title", ""),
            "tanggal": a.get("pubDate", ""),
            "konten": a.get("description", ""),
            "link": link
        })

    print(f"Total berita API: {len(data)}")
    print(f"Berita baru: {len(news)}")
    print(f"Berita dilewati: {len(seen_links) - len(news)}")

    return news
