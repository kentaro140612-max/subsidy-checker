import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI
import re

# 日本標準時
now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def ai_analyze(title):
    # 【確認方法1：APIエラーの検知】
    # このtry-except文により、APIキーが無効、または予算切れの場合、
    # 下記のexcept節が実行され、サイト上に「要確認」と表示されます。
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """補助金タイトルを分析し、以下形式で出力せよ。
1. 要約：(30文字以内の概要)
2. 金額：(「最大◯◯万円」や「実費」など。不明なら「要確認」)
3. スコア：(★1-5)"""},
                {"role": "user", "content": title}
            ],
            max_tokens=250
        )
        res_text = response.choices[0].message.content
        summary = res_text.split("2. 金額：")[0].replace("1. 要約：", "").strip()
        amount = res_text.split("2. 金額：")[1].split("3. スコア：")[0].strip()
        score = res_text.split("3. スコア：")[1].strip() if "3. スコア：" in res_text else "★★★"
        return summary, amount, score
    except Exception as e:
        # エラー時はここに飛ぶ。ログを確認するにはGitHub Actionsの実行詳細を見る。
        print(f"DEBUG: AI Analysis Error: {e}")
        return "公式資料を確認してください。", "要確認", "★★★"

def generate_html(subsidies):
    list_items = ""
    for item in subsidies:
        summary, amount, score = ai_analyze(item['title'])
        list_items += f"""
        <article style="border: 1px solid #eee; padding: 25px; margin-bottom: 25px; border-radius: 15px; background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                <h2 style="color: #1a73e8; font-size: 1.1rem; margin: 0; flex: 1; padding-right: 10px;">{item['title']}</h2>
                <span style="color: #e65100; font-weight: bold; white-space: nowrap;">{score}</span>
            </div>
            <div style="margin-bottom: 15px;">
                <span style="background: #e8f0fe; color: #1967d2; font-size: 0.8rem; padding: 4px 12px; border-radius: 20px; font-weight: bold; border: 1px solid #1a73e8;">{amount}</span>
            </div>
            <p style="font-size: 0.9rem; line-height: 1.6; color: #3c4043; margin-bottom: 20px;">{summary}</p>
            <a href="{item['link']}" target="_blank" style="display: block; text-align: center; background: #1a73e8; color: #fff; padding: 12px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 0.9rem;">公式資料を詳しく見る</a>
        </article>"""
    
    # フッターに「免責事項」を追加し、透明性を確保
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AI補助金ナビ</title></head><body style="max-width: 600px; margin: 0 auto; background: #f1f3f4; padding: 20px; font-family: sans-serif;"><h1>AI補助金ナビ</h1><p style="color: #5f6368; font-size: 0.8rem; margin-bottom: 30px;">最終更新：{now}</p><main>{list_items}</main><footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ccc; color: #70757a; font-size: 0.75rem; line-height: 1.6;"><p>【免責事項】<br>本サイトはAIを用いて情報を自動収集・要約しています。正確な情報は必ずリンク先の公式資料をご確認ください。本サイトの情報を利用したことによる損害について、当方は一切の責任を負いません。</p></footer></body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

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
            data.append({{"title": title, "link": full_url}})
            seen_titles.add(title)
            if len(data) >= 5: break
    return data

if __name__ == "__main__":
    subsidies = fetch_data()
    if subsidies:
        generate_html(subsidies)
