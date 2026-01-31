import os, requests, re
from bs4 import BeautifulSoup

SOURCE_NAME = "J-Net21（中小機構）"
SOURCE_URL = "https://j-net21.smrj.go.jp/snavi/articles"

def fetch_clean_data():
    try:
        res = requests.get(SOURCE_URL, timeout=20)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/snavi/articles/\d+'))
        
        data = []
        seen = set()
        for a in links:
            t = a.get_text(strip=True)
            if len(t) > 12 and t not in seen:
                h = a.get('href')
                full_url = h if h.startswith('http') else "https://j-net21.smrj.go.jp" + h
                data.append({"title": t, "link": full_url})
                seen.add(t)
                if len(data) >= 30: break
        return data
    except Exception as e:
        print(f"Error: {e}")
        return []

def generate_html(subsidies):
    list_items = ""
    for item in subsidies:
        list_items += f"""
        <article style="padding:25px 0; border-bottom:1px solid #edf2f7;">
            <h2 style="font-size:1.1rem; line-height:1.6; margin:0 0 16px 0; color:#2d3748; font-weight:700;">{item['title']}</h2>
            <a href="{item['link']}" target="_blank" style="display:inline-block; background:#2b6cb0; color:#fff; padding:12px 25px; text-decoration:none; border-radius:8px; font-size:0.9rem; font-weight:bold;">J-Net21で詳細を確認</a>
        </article>"""
    
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>補助金速報</title></head>
<body style="max-width:600px; margin:0 auto; background:#f7fafc; padding:40px 20px; font-family:sans-serif;">
    <header style="margin-bottom:40px; border-bottom:2px solid #2b6cb0; padding-bottom:20px;">
        <h1 style="font-size:1.7rem; color:#2b6cb0; margin:0;">補助金速報</h1>
        <p style="font-size:0.9rem; color:#718096; margin-top:10px;">J-Net21最新30件：ノイズを排した最短アクセス</p>
    </header>
    <main style="background:#fff; padding:0 25px; border-radius:12px; border:1px solid #e2e8f0;">{list_items}</main>
</body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    data = fetch_clean_data()
    if data: generate_html(data)
