import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI

# 日本標準時
now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def ai_analyze(title):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "補助金タイトルを分析し、要約とおすすめ度(★1-5)を出力せよ。形式：要約：(内容) / スコア：(星)"},
                {"role": "user", "content": title}
            ],
            max_tokens=250
        )
        res_text = response.choices[0].message.content
        summary = res_text.split("スコア：")[0].replace("要約：", "").strip().replace('\n', '<br>')
        score = res_text.split("スコア：")[1].strip() if "スコア：" in res_text else "★★★"
        return summary, score
    except:
        return "詳細は公式資料を確認してください。", "★★★"

def generate_html_and_sitemap(subsidies):
    google_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSddIW5zNLUuZLyQWIESX0EOZWZUM3dGM6pdW9Luw20YTiEuwg/viewform?usp=dialog"
    list_items = ""
    for item in subsidies:
        summary, score = ai_analyze(item['title'])
        list_items += f"""
        <article style="border: 1px solid #eee; padding: 25px; margin-bottom: 25px; border-radius: 15px; background: #fff;">
            <div style="display: flex; justify-content: space-between;">
                <h2 style="color: #1a73e8; font-size: 1.1rem;">{item['title']}</h2>
                <span style="color: #e65100; font-weight: bold;">{score}</span>
            </div>
            <p style="font-size: 0.9rem; line-height: 1.6;">{summary}</p>
            <div style="display: flex; gap: 10px;">
                <a href="{item['link']}" target="_blank" style="flex: 1; text-align: center; border: 1px solid #ccc; padding: 10px; text-decoration: none; border-radius: 5px; color: #333;">公式資料</a>
                <a href="{google_form_url}" target="_blank" style="flex: 1; text-align: center; background: #1a73e8; color: #fff; padding: 10px; text-decoration: none; border-radius: 5px;">無料相談</a>
            </div>
        </article>
        """
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AI補助金ナビ</title></head><body style="max-width: 600px; margin: 0 auto; background: #f1f3f4; padding: 20px; font-family: sans-serif;"><h1>AI補助金ナビ</h1><p>最終更新：{now}</p><main>{list_items}</main></body></html>"""
    
    print(f"HTML Content length: {len(html_content)}")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def fetch_data():
    res = requests.get("https://j-net21.smrj.go.jp/snavi/articles", timeout=30)
    soup = BeautifulSoup(res.text, 'html.parser')
    articles = soup.find_all('h3')[:5]
    return [{"title": a.get_text(strip=True), "link": "https://j-net21.smrj.go.jp" + a.find('a')['href']} for a in articles if a.find('a')]

if __name__ == "__main__":
    subsidies = fetch_data()
    if subsidies:
        generate_html_and_sitemap(subsidies)
        print(f"Success: {len(subsidies)} articles updated.")
