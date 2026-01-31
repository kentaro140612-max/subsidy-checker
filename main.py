import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI
import re
import hashlib

# 日本標準時
now_dt = datetime.now()
now = now_dt.strftime('%Y年%m月%d日 %H:%M')
sitemap_date = now_dt.strftime('%Y-%m-%d')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
    """英数字IDを使用した個別ページ生成"""
    file_path = f"articles/{file_id}.html"
    tag_html = "".join([f'<span style="background:#eee; padding:2px 8px; margin-right:5px; border-radius:5px; font-size:0.8rem;">#{t.strip()}</span>' for t in tags.split(",")])
    
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['title']}</title></head>
    <body style="max-width:600px; margin:0 auto; padding:40px 20px; font-family:sans-serif; line-height:1.6; color:#333; background:#f9f9f9;">
        <a href="../index.html" style="color:#1a73e8; text-decoration:none;">← 一覧へ戻る</a>
        <p style="font-size:0.8rem; color:#666; margin-top:20px;">更新日：{now}</p>
        <h1 style="font-size:1.4rem; margin-top:10px;">{item['title']}</h1>
        <div style="margin-bottom:20px;">{tag_html}</div>
        <div style="background:#fff; padding:20px; border-radius:10px; border:1px solid #eee; margin-bottom:20px;">
            <p style="color:#e65100; font-weight:bold; font-size:1.2rem; margin:0;">金額：{amount}</p>
            <p style="margin:10px 0 0 0; color:#555;">おすすめ度：{score}</p>
        </div>
        <p>{summary}</p>
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
        lines.append(f'  <url><loc>{base_url}{url}</loc><lastmod>{sitemap_date}</lastmod><priority>0.8</priority></url>')
    lines.append('</urlset>')
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def generate_html(subsidies):
    list_items = ""
    article_urls = []
    for i, item in enumerate(subsidies):
        summary, amount, score, tags = ai_analyze(item['title'])
        # タイトルからハッシュ値を生成し、英数字のみのファイル名にする
        file_id = hashlib.md5(item['title'].encode()).hexdigest()[:12] + f"_{i}"
        page_path = generate_individual_page(item, summary, amount, score, tags, file_id)
        article_urls.append(page_path)
        
        tag_elements = "".join([f'<span style="font-size:0.65rem; background:#f0f0f0; color:#555; padding:2px 8px; border-radius:4px; margin-right:4px; border:1px solid #ddd;">{t.strip()}</span>' for t in tags.split(",")])
        
        list_items += f"""
        <article style="border: 1px solid #eee; padding: 25px; margin-bottom: 25px; border-radius: 15px; background: #fff; box-
