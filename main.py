import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI

# 物理定数・単位の厳守: 日本標準時
now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def ai_analyze(title):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "補助金タイトルを分析し、経営者向けに【3箇条の要約】と【おすすめ度(★1-5)】を出力せよ。特に『返済不要』『受給額』に触れること。出力形式：要約：(要約テキスト) / スコア：(星の数)"},
                {"role": "user", "content": title}
            ],
            max_tokens=250
        )
        res_text = response.choices[0].message.content
        summary = res_text.split("スコア：")[0].replace("要約：", "").strip().replace('\n', '<br>')
        score = res_text.split("スコア：")[1].strip() if "スコア：" in res_text else "★★★"
        return summary, score
    except Exception as e:
        print(f"AI Error: {e}")
        return "・詳細は公式資料を確認してください。", "★★★"

def generate_html_and_sitemap(subsidies):
    google_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSddIW5zNLUuZLyQWIESX0EOZWZUM3dGM6pdW9Luw20YTiEuwg/viewform?usp=dialog"
    
    list_items = ""
    for item in subsidies:
        summary, score = ai_analyze(item['title'])
        list_items += f"""
        <article style="border: 1px solid #eee; padding: 25px; margin-bottom: 25px; border-radius: 15px; background: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <h2 style="color: #1a73e8; margin-top: 0; font-size: 1.2rem; line-height: 1.4; flex: 1;">{item['title']}</h2>
                <span style="background: #fff3e0; color: #e65100; padding: 4px 8px; border-radius: 5px; font-weight: bold; font-size: 0.8rem; margin-left: 10px;">おすすめ：{score}</span>
            </div>
            <div style="background: #fff9f9; border: 1px solid #ffebee; padding: 15px; border-radius: 10px; margin: 15px 0; font-size: 0.95rem; line-height: 1.8;">
                <strong style="color: #d93025;">▼ AI解析：返済不要情報など</strong><br>
                {summary}
            </div>
            <div style="display: flex; gap: 10px;">
                <a href="{item['link']}" target="_blank" style="flex: 1; text-align: center; border: 1px solid #dadce0; padding: 12px; text-decoration: none; border-radius: 8px; color: #3c4043; font-weight: bold; font-size: 0.8rem;">公式資料</a>
                <a href="{google_form_url}" target="_blank" style="flex: 1; text-align: center; background: #1a73e8; color: white; padding: 12px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 0.8rem;">プロに無料相談</a>
            </div>
        </article>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="google-site-verification" content="qDKunZB9hZN753KuLftIbJUXeWBi3bA-HfSS-gej1KA" />
        <title>AI補助金要約ナビ | 2026年最新版</title>
        <meta name="description" content="AIが補助金を即座に解析しおすすめ度を判定。">
    </head>
    <body style="max-width: 600px; margin: 0 auto; background: #f1f3f4; padding: 20px; font-family: sans-serif; color: #202124;">
        <header style="text-align: center; padding: 30px 0;">
            <h1 style="font-size: 1.7rem; margin-bottom: 5px;">AI補助金要約ナビ</h1>
            <p style="color: #5f6368; font-size: 0.9rem;">最終更新：{now}</p>
        </header>
        <main>{list_items if list_items else "<p style='text-align:center;'>現在、新規の補助金情報はありません。</p>"}</main>
        <footer style="text-align: center; margin-top: 50px; color: #70757a; font-size: 0.8rem;">
            &copy; 2026 AI Subsidy Navigation.
        </footer>
    </body>
    </html>
    """
    # ログ出力: 書き込み直前に文字数を確認
    print(f"HTML Content length: {len(html_content)}")
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://kentaro140612-max.github.io/subsidy-checker/</loc><lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod><priority>1.0</priority></url>
    </urlset>"""
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_content)

def fetch_data():
    url = "https://j-net21.smrj.go.jp/snavi/articles"
    res = requests.get(url, timeout=30)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    articles = soup.find_all('h3')[:5] # A案：上位5件に厳選
    data = []
    for art in articles:
        link_tag = art.find('a')
        if link_tag and link_tag.get('href'):
            data.append({"title": art.get_text(strip=True), "link": "https://j-net21.smrj.go.jp" + link_tag['href']})
    return data

if __name__ == "__main__":
    try:
        subsidies = fetch_data()
        if subsidies:
            generate_html_and_sitemap(subsidies)
            print(f"Success: {len(subsidies)} articles updated.")
        else:
            print("Warning: No articles found.")
    except Exception as e:
        print(f"Critical Error: {e}")
