import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# [物理単位の厳守]: 日本時間を基準とした更新日の取得
now = datetime.now().strftime('%Y年%m月%d日 %H:%M')

def generate_html(subsidies):
    # フォームURLの指定（必ず https://docs.google.com/forms/d/e/.../viewform の形式にすること）
    google_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSddIW5zNLUuZLyQWIESX0EOZWZUM3dGM6pdW9Luw20YTiEuwg/viewform?usp=publish-editor"

    list_items = ""
    for item in subsidies:
        list_items += f"""
        <article style="border: 1px solid #eee; padding: 20px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <h2 style="color: #2c3e50; margin-top: 0; font-size: 1.2rem;">{item['title']}</h2>
            <p style="font-size: 0.9rem; color: #666;">
                <strong>地域:</strong> 全国 | <strong>カテゴリー:</strong> 経営支援
            </p>
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <a href="{item['link']}" target="_blank" style="flex: 1; text-align: center; background: #f8f9fa; color: #333; padding: 10px; text-decoration: none; border-radius: 5px; border: 1px solid #ddd; font-weight: bold; font-size: 0.9rem;">公式詳細を見る</a>
                <a href="{google_form_url}" target="_blank" style="flex: 1; text-align: center; background: #28a745; color: white; padding: 10px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 0.9rem;">専門家に無料相談</a>
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
        <title>【最新】自治体補助金自動集約ナビ 2026</title>
    </head>
    <body style="max-width: 800px; margin: 40px auto; padding: 0 20px; font-family: sans-serif; line-height: 1.6; color: #333;">
        <header style="border-bottom: 3px solid #007bff; margin-bottom: 30px; padding-bottom: 10px;">
            <h1 style="margin: 0; font-size: 1.8rem;">自治体補助金自動集約ナビ</h1>
            <p style="color: #888; font-size: 0.9rem;">最終自動更新: {now}</p>
        </header>
        <main>{list_items}</main>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def fetch_data():
    url = "https://j-net21.smrj.go.jp/snavi/articles"
    res = requests.get(url, timeout=30)
    soup = BeautifulSoup(res.text, 'html.parser')
    articles = soup.select('h3')[:10]
    data = []
    for art in articles:
        link_tag = art.find('a')
        data.append({{"title": art.get_text(strip=True), "link": "https://j-net21.smrj.go.jp" + link_tag['href'] if link_tag else url}})
    return data

if __name__ == "__main__":
    try:
        generate_html(fetch_data())
        print("Success: index.html updated.")
    except Exception as e:
        print(f"Error: {{e}}")
