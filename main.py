import os, requests, re
from bs4 import BeautifulSoup

SOURCE_NAME = "J-Net21（独立行政法人 中小企業基盤整備機構）"
SOURCE_URL = "https://j-net21.smrj.go.jp/snavi/articles"

def fetch_data():
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
        # 文言を「詳細を確認する（J-Net21）」に物理的に修正
        list_items += f"""
        <div style="padding:28px 0; border-bottom:1px solid #E2E8F0;">
            <h2 style="font-size:1.15rem; line-height:1.6; margin:0 0 20px 0; color:#1A202C; font-weight:700;">{item['title']}</h2>
            <a href="{item['link']}" target="_blank" style="background-color:#2B6CB0 !important; color:#FFFFFF !important; padding:14px 28px; text-decoration:none; border-radius:8px; font-size:0.95rem; font-weight:bold; display:inline-block; transition: opacity 0.2s;">詳細を確認する (J-Net21)</a>
        </div>"""
    
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>補助金速報</title></head>
<body style="max-width:640px; margin:0 auto; background-color:#F8FAFC; padding:40px 20px; font-family:sans-serif;">
    <header style="margin-bottom:40px; border-left:6px solid #2B6CB0; padding-left:20px;">
        <h1 style="font-size:2rem; margin:0; color:#1A202C; letter-spacing:-0.02em;">補助金速報</h1>
        <p style="font-size:1rem; color:#718096; margin-top:10px;">J-Net21 公募情報：最新30件を同期中</p>
    </header>
    <main style="background-color:#FFFFFF; padding:10px 30px; border-radius:16px; border:1px solid #E2E8F0; box-shadow:0 4px 12px rgba(0,0,0,0.05);">
        {list_items}
    </main>
    <footer style="margin-top:60px; text-align:center; color:#A0AEC0; font-size:0.8rem;">
        <p>出典：{SOURCE_NAME}</p>
        <p style="margin-top:8px;">24時間ごとに自動更新を実行中</p>
    </footer>
</body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    data = fetch_data()
    if data:
        generate_html(data)
