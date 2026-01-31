import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI
import re

# 日本標準時
now_dt = datetime.now()
now = now_dt.strftime('%Y年%m月%d日 %H:%M')
sitemap_date = now_dt.strftime('%Y-%m-%d')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 物理保存用のディレクトリ作成
os.makedirs("articles", exist_ok=True)

def ai_analyze(title):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "補助金タイトルを分析しSEOを意識して出力せよ。1. 要約：(30文字以内の概要) 2. 金額：(最大◯◯万円) 3. スコア：(★1-5) 4. タグ：(業種等3つ)"},
                {"role": "user", "content": title}
            ],
            max_tokens=300
        )
        res_text = response.choices[0].message.content
        summary = res_text.split("2. 金額：")[0].replace("1. 要約：", "").strip()
        amount = res_text.split("2. 金額：")[1].split("3. スコア：")[0].strip()
        parts = res_text.split("3. スコア：")[1].split("4. タグ：")
        score = parts[0].strip()
        tags = parts[1].strip() if len(parts) > 1 else "補助金, 最新"
        return summary, amount, score, tags
    except:
        return "公式資料を確認してください。", "要確認", "★★★", "補助金, 最新"

def generate_individual_page(item, summary, amount, score, tags, file_id):
    file_path = f"articles/{file_id}.html"
    tag_html = "".join([f'<span style="background:#eee; padding:2px 8px; margin-right:5px; border-radius:5px;">#{t.strip()}</span>' for t in tags.split(",")])
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['title']} | AI補助金ナビ</title></head>
    <body style="max-width:600px; margin:0 auto; padding:40px 20px; font-family:sans-serif; line-height:1.6; color:#333; background:#f9f9f9;">
        <a href="../index.html" style="color:#1a73e8; text-decoration:none;">← 一覧へ戻る</a>
        <p style="font-size:0.8rem; color:#666; margin-top:20px;">更新日：{now}</p>
        <h1 style="font-size:1.5rem; margin-top:10px;">{item['title']}</h1>
        <div style="background:#fff; padding:20px; border-radius:10px; border:1px solid #eee; margin-bottom:20px;">
            <p style="color:#e65100; font-weight:bold; font-size:1.2rem; margin:0;">金額：{amount}</p>
            <p style="margin:10px 0 0 0; color:#555;">おすすめ度：{score}</p>
        </div>
        <div style="background:#fff; padding:20px; border-radius:10px; border:1px solid #eee;">
            <p>{summary}</p>
        </div>
        <div style="margin-top:30px;">
            <a href="{item['link']}" target="_blank" style="display:block; text-align:center; background:#1a73e8; color:#fff; padding:15px; text-decoration:none; border-radius:8px; font-weight:bold;">公式資料を確認する</a>
        </div>
    </body></html>"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    return file_path

def generate_sitemap(urls):
    base_url = "https://smart-guidance-lab.github.io/hojokin-navi/"
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines.append(f'  <url><loc>{base_url}index.html</loc><lastmod>{sitemap_date}</lastmod><priority>1.0</priority></url>')
    for url in urls:
        full_url = f"{base_url}{url}"
        lines.append(f'  <url><loc>{full_url}</loc><lastmod>{sitemap_date}</lastmod><priority>0.8</priority></url>')
    lines.append('</urlset>')
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("DEBUG: sitemap.xml has been generated.")

def generate_html(subsidies):
    list_items = ""
    article_urls = []
    for i, item in enumerate(subsidies):
        summary, amount, score, tags = ai_analyze(item['title'])
        file_id = re.sub(r'[^\w\s-]', '', item['title'])[:20].strip().replace(' ', '_') + f"_{i}"
        page_path = generate_individual_page(item, summary, amount, score, tags, file_id)
        article_urls.append(page_path)
        list_items += f"""
        <article style="border: 1px solid #eee; padding: 25px; margin-bottom: 25px; border-radius: 15px; background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <p style="font-size:0.7rem; color:#5f6368; margin-bottom:5px;">更新：{now}</p>
            <h2 style="color: #1a73e8; font-size: 1.1rem; margin-bottom:10px;">{item['title']}</h2>
            <p style="font-size: 0.9rem; color: #3c4043; margin-bottom: 15px;">{summary}</p>
            <div style="display:flex; gap:10px;">
                <a href="{page_path}" style="flex:1; text-align:center; border:1px solid #1a73e8; color:#1a73e8; padding:10px; text-decoration:none; border-radius:5px; font-size:0.8rem;">詳細を見る</a>
                <a href="{item['link']}" target="_blank" style="flex:1; text-align:center; background:#1a73e8; color:#fff; padding:10px; text-decoration:none; border-radius:5px; font-size:0.8rem;">公式資料</a>
            </div>
        </article>"""
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="qDKunZB9hZN753KuLftIbJUXeWBi3bA-HfSS-gej1KA" />
    <meta name="description" content="AIが最新の補助金情報を要約。最短1分で自分に合った補助金が見つかる。"><title>AI補助金ナビ | smart-guidance-lab</title></head>
    <body style="max-width: 600px; margin: 0 auto; background: #f1f3f4; padding: 20px; font-family: sans-serif;">
        <h1 style="color:#202124;">AI補助金ナビ</h1>
        <p style="color: #5f6368; font-size: 0.8rem; margin-bottom: 30px;">最終更新：{now}</p>
        <main>{list_items}</main>
        <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ccc; color: #70757a; font-size: 0.75rem; line-height: 1.6;">
            <p>【免責事項】本サイトはAIを用いて情報を自動収集・要約しています。正確な情報は必ず公式資料をご確認ください。</p>
        </footer>
    </body></html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    generate_sitemap(article_urls)

def fetch_data():
    url = "https://j-net21.smrj.go.jp/snavi/articles"
    res = requests.get(url, timeout=30)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    all_links = soup.find_all('a', href=re.compile(r'/snavi/articles/\d+'))
    data = []
    seen_titles = set()
    for a in all_links:
        title = a.get_text(strip=True)
        href = a.get('href')
        if len(title) > 5 and title not in seen_titles:
            full_url = href if href.startswith('http') else "https://j-net21.smrj.go.jp" + href
            data.append({"title": title, "link": full_url})
            seen_titles.add(title)
            if len(data) >= 10: break
    return data

if __name__ == "__main__":
    subsidies = fetch_data()
    if subsidies:
        generate_html(subsidies)
