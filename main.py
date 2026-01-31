import os, requests, re, json
from bs4 import BeautifulSoup
from datetime import datetime

DATA_FILE = "subsidies_db.json"
SOURCE_URL = "https://j-net21.smrj.go.jp/snavi/articles"

# 抽出キーワード定義（収益化に直結する単語を優先）
TAG_KEYWORDS = {
    "創業": "#E53E3E", "起業": "#E53E3E",
    "DX": "#3182CE", "IT": "#3182CE", "システム": "#3182CE",
    "省エネ": "#38A169", "脱炭素": "#38A169",
    "展示会": "#805AD5", "販路": "#805AD5"
}

def fetch_and_merge():
    print("Starting data fetch...")
    db = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
        except: db = []
    
    try:
        res = requests.get(SOURCE_URL, timeout=20)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.find_all('a', href=re.compile(r'/snavi/articles/\d+'))
        
        seen_titles = {item['title'] for item in db}
        new_items = []
        
        for a in links:
            title = a.get_text(strip=True)
            if len(title) > 12 and title not in seen_titles:
                # タグの抽出
                tags = [k for k in TAG_KEYWORDS.keys() if k in title]
                href = a.get('href')
                url = href if href.startswith('http') else "https://j-net21.smrj.go.jp" + href
                new_items.append({
                    "title": title, "link": url, 
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "tags": tags
                })
                seen_titles.add(title)

        updated_db = (new_items + db)[:1000]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_db, f, ensure_ascii=False, indent=2)
        print(f"Update successful. New items: {len(new_items)}.")
        return updated_db
    except Exception as e:
        print(f"Error: {e}"); return db

def generate_html(db):
    print("Generating index.html...")
    list_items = ""
    for item in db[:100]:
        # タグのHTML生成
        tag_html = "".join([f'<span style="background:{TAG_KEYWORDS.get(t, "#718096")}; color:white; padding:2px 8px; border-radius:4px; font-size:0.7rem; margin-right:5px;">{t}</span>' for t in item.get('tags', [])])
        
        list_items += f"""
        <div style="padding:20px 0; border-bottom:1px solid #E2E8F0;">
            <div style="margin-bottom:8px;">{tag_html}</div>
            <p style="font-size:0.8rem; color:#A0AEC0; margin:0;">{item.get('date', '不明')}</p>
            <h2 style="font-size:1.1rem; margin:5px 0 15px 0; font-weight:700; line-height:1.4;">{item['title']}</h2>
            <a href="{item['link']}" target="_blank" style="background-color:#2B6CB0; color:#FFFFFF; padding:10px 20px; text-decoration:none; border-radius:5px; font-size:0.85rem; font-weight:bold; display:inline-block;">詳細を確認</a>
        </div>"""

    html_content = f"""<!DOCTYPE html><html lang="ja">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>補助金データベース | 自律成長型資産</title></head>
<body style="max-width:640px; margin:0 auto; padding:40px 20px; font-family:sans-serif; background-color:#F8FAFC; color:#2D3748;">
    <header style="background:#FFFFFF; padding:25px; border-radius:12px; margin-bottom:30px; border:1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
        <h1 style="margin:0; font-size:1.4rem; color:#2B6CB0;">補助金・助成金データベース</h1>
        <p style="font-size:0.9rem; color:#718096; margin-top:8px;">現在 <strong>{len(db)}</strong> 件の情報を蓄積・解析中</p>
    </header>
    <main style="background:#FFFFFF; padding:0 25px; border-radius:12px; border:1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
        {list_items}
    </main>
    <footer style="text-align:center; margin-top:30px; color:#A0AEC0; font-size:0.75rem;">
        自律型クロールシステム稼働中<br>最終更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </footer>
</body></html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    generate_html(fetch_and_merge())
