import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from openai import OpenAI
import re
import hashlib
import glob

# 日本標準時
now_dt = datetime.now()
now = now_dt.strftime('%Y年%m月%d日 %H:%M')
sitemap_date = now_dt.strftime('%Y-%m-%d')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

os.makedirs("articles", exist_ok=True)

def cleanup_old_files():
    """日本語名の旧ファイルや不要なファイルを物理削除する"""
    files = glob.glob("articles/*.html")
    for f in files:
        filename = os.path.basename(f)
        # 英数字12文字+アンダースコア+数字 以外の形式（古い日本語名など）を削除
        if not re.match(r'^[a-f0-9]{12}_\d+\.html$', filename):
            try:
                os.remove(f)
                print(f"DELETED: {filename}")
            except: pass

def ai_analyze(title):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """補助金を分析し、以下の4つのカテゴリーから最も適切な1つを選び、続けて要約・金額・スコアを出力せよ。
カテゴリー：[製造・建設, IT・DX, 商業・サービス, その他]
形式：
カテゴリ：(1つ選ぶ)
要約：(30文字以内)
金額：(最大◯◯万円)
スコア：(★1-5)"""},
                {"role": "user", "content": title}
            ],
            max_tokens=300
        )
        res_text = response.choices[0].message.content
        cat = res_text.split("要約：")[0].replace("カテゴリ：", "").strip()
        summary = res_text.split("要約：")[1].split("金額：")[0].strip()
        amount = res_text.split("金額：")[1].split("スコア：")[0].strip()
        score = res_text.split("スコア：")[1].strip()
        return cat, summary, amount, score
    except:
        return "その他", "公式資料を確認してください。", "要確認", "★★★"

def generate_individual_page(item, cat, summary, amount, score, file_id):
    file_path = f"articles/{file_id}.html"
    # 簡易アーカイブ警告（3日以上前の記事に表示する想定のロジック基盤）
    warning_html = '<div style="background:#fff3e0; border:1px solid #ffe0b2; padding:10px; border-radius:5px; margin-bottom:20px; font-size:0.8rem; color:#e65100;">⚠️ この情報は公開から時間が経過しています。最新の募集状況は必ず公式資料をご確認ください。</div>'
    
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['title']}</title></head>
<body style="max-width:600px; margin:0 auto; padding:40px 20px; font-family:sans-serif; line-height:1.6; color:#333; background:#f9f9f9;">
    <a href="../index.html" style="color:#1a73e8; text-decoration:none;">← 一覧へ戻る</a>
    <p style="font-size:0.8rem; color:#666; margin-top:20px;">更新日：{now}</p>
    {warning_html}
    <div style="display:inline-block; background:#1a73e8; color:#fff; font-size:0.7rem; padding:2px 8px; border-radius:4px;">{cat}</div>
    <h1 style="font-size:1.4rem; margin-top:10px;">{item['title']}</h1>
    <div style="background:#fff; padding:20px; border-radius:10px; border:1px solid #eee; margin-bottom:20px;">
        <p style="color:#e65100; font-weight:bold; font-size:1.2rem; margin:0;">金額：{amount}</p>
        <p style="margin:10px 0 0 0; color:#555;">おすすめ度：{score}</p>
    </div>
    <p>{summary}</p>
    <div style="margin-top:30px;"><a href="{item['link']}" target="_blank" style="display:block; text-align:center; background:#1a73e8; color:#fff; padding:15px; text-decoration:none; border-radius:8px; font-weight:bold;">公式資料を確認する（外部）</a></div>
</body></html>"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    return file_path

def generate_html(subsidies):
    cleanup_old_files() # 実行前に掃除
    list_items = ""
    article_urls = []
    for i, item in enumerate(subsidies):
        cat, summary, amount, score = ai_analyze(item['title'])
        file_id = hashlib.md5(item['title'].encode()).hexdigest()[:12] + f"_{i}"
        page_path = generate_individual_page(item, cat, summary, amount, score, file_id)
        article_urls.append(page_path)
        
        list_items += f"""
        <article style="border: 1px solid #eee; padding: 20px; margin-bottom: 20px; border-radius: 12px; background: #fff;">
            <div style="font-size:0.65rem; color:#1a73e8; font-weight:bold; margin-bottom:5px;">【{cat}】</div>
            <h2 style="font-size:1rem; margin:0 0 10px 0; color:#202124;">{item['title']}</h2>
            <p style="font-size:0.85rem; color:#5f6368; margin-bottom:15px;">{summary}</p>
            <div style="display:flex; gap:10px;">
                <a href="{page_path}" style="flex:1; text-align:center; border:1px solid #1a73e8; color:#1a73e8; padding:8px; text-decoration:none; border-radius:6px; font-size:0.8rem;">詳細を見る</a>
                <a href="{item['link']}" target="_blank" style="flex:1; text-align:center; background:#1a73e8; color:#fff; padding:8px; text-decoration:none; border-radius:6px; font-size:0.8rem;">公式資料</a>
            </div>
        </article>"""
    
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-site-verification" content="qDKunZB9hZN753KuLftIbJUXeWBi3bA-HfSS-gej1KA" />
<title>AI補助金ナビ</title></head>
<body style="max-width: 600px; margin: 0 auto; background: #f1f3f4; padding: 20px; font-family: sans-serif;">
    <h1 style="font-size:1.5rem; margin-bottom:20px;">AI補助金ナビ</h1>
    <main>{list_items}</main>
</body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
    
    base_url = "https://smart-guidance-lab.github.io/hojokin-navi/"
    s_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    s_lines.append(f'  <url><loc>{base_url}index.html</loc><lastmod>{sitemap_date}</lastmod><priority>1.0</priority></url>')
    for u in article_urls: s_lines.append(f'  <url><loc>{base_url}{u}</loc><lastmod>{sitemap_date}</lastmod><priority>0.8</priority></url>')
    s_lines.append('</urlset>')
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write("\n".join(s_lines))

def fetch_data():
    url = "https://j-net21.smrj.go.jp/snavi/articles"
    res = requests.get(url, timeout=30)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    all_links = soup.find_all('a', href=re.compile(r'/snavi/articles/\d+'))
    data = []
    seen = set()
    for a in all_links:
        t = a.get_text(strip=True)
        h = a.get('href')
        if len(t) > 5 and t not in seen:
            f_url = h if h.startswith('http') else "https://j-net21.smrj.go.jp" + h
            data.append({"title": t, "link": f_url})
            seen.add(t)
            if len(data) >= 10: break
    return data

if __name__ == "__main__":
    try:
        subsidies = fetch_data()
        if subsidies: generate_html(subsidies)
    except Exception as e: print(f"Error: {e}")
