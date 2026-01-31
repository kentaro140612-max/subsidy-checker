import os, requests, re, hashlib, glob, json
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI

# 構成設定
SOURCE_NAME = "J-Net21（独立行政法人 中小企業基盤整備機構）"
SOURCE_URL = "https://j-net21.smrj.go.jp/"
now_dt = datetime.now()
now = now_dt.strftime('%Y年%m月%d日 %H:%M')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

os.makedirs("articles", exist_ok=True)

def cleanup_old_files():
    for f in glob.glob("articles/*.html"):
        if not re.match(r'^[a-f0-9]{12}_\d+\.html$', os.path.basename(f)):
            try: os.remove(f)
            except: pass

def ai_analyze(title):
    """JSONモードを使用してAIの出力を完全に制御する"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": """補助金タイトルを分析しJSONで返せ。
項目: category(製造・建設, IT・DX, 商業・サービス, その他), target(対象者), usage(支援対象となる活動), amount(推定金額感:「〜50万円」「100万円以上」等。'参照'は禁止), score(1から5の整数のみ)"""},
                {"role": "user", "content": title}
            ]
        )
        data = json.loads(response.choices[0].message.content)
        
        # スコアの正規化（1-5の数字を星に変換）
        raw_score = int(data.get("score", 3))
        score_val = max(1, min(5, raw_score))
        star_score = '★' * score_val + '☆' * (5 - score_val)
        
        return {
            "cat": data.get("category", "その他"),
            "target": data.get("target", "事業者"),
            "usage": data.get("usage", "公的資料を確認"),
            "amount": data.get("amount", "10万円〜(規模より推計)"),
            "score": star_score
        }
    except Exception:
        return {"cat": "その他", "target": "要資料確認", "usage": "詳細を確認", "amount": "10万円〜(推計)", "score": "★★★☆☆"}

def generate_individual_page(item, info, file_id):
    file_path = f"articles/{file_id}.html"
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['title']}</title></head>
<body style="max-width:600px; margin:0 auto; padding:40px 20px; font-family:sans-serif; line-height:1.6; color:#333; background:#f0f2f5;">
    <a href="../index.html" style="color:#1a73e8; text-decoration:none; font-weight:bold; font-size:0.9rem;">← 一覧へ戻る</a>
    <h1 style="font-size:1.3rem; margin:25px 0; color:#1c1e21; line-height:1.4; border-bottom:2px solid #1a73e8; padding-bottom:10px;">{item['title']}</h1>
    
    <div style="background:#fff; padding:30px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.1); margin-bottom:30px;">
        <h3 style="margin:0 0 20px 0; font-size:0.9rem; color:#606770; text-transform:uppercase;">簡易要約（AI推定）</h3>
        <table style="width:100%; border-collapse:collapse; font-size:0.95rem;">
            <tr style="border-bottom:1px solid #ebedf0;"><td style="padding:15px 0; color:#606770; width:45%;">カテゴリ</td><td style="padding:15px 0; font-weight:bold; color:#1a73e8;">{info['cat']}</td></tr>
            <tr style="border-bottom:1px solid #ebedf0;"><td style="padding:15px 0; color:#606770;">主な対象者</td><td style="padding:15px 0; font-weight:bold;">{info['target']}</td></tr>
            <tr style="border-bottom:1px solid #ebedf0;"><td style="padding:15px 0; color:#606770;">支援対象となる活動</td><td style="padding:15px 0; font-weight:bold;">{info['usage']}</td></tr>
            <tr style="border-bottom:1px solid #ebedf0;"><td style="padding:15px 0; color:#606770;">推定補助金額</td><td style="padding:15px 0; font-weight:bold; color:#d32f2f;">{info['amount']}</td></tr>
            <tr><td style="padding:15px 0; color:#606770;">AIおすすめ度</td><td style="padding:15px 0; font-weight:bold; color:#f5c33b; letter-spacing:3px; font-family:monospace; font-size:1.2rem;">{info['score']}</td></tr>
        </table>
    </div>

    <div style="background:#1a73e8; padding:35px; border-radius:12px; text-align:center;">
        <p style="color:#fff; font-size:0.9rem; margin:0 0 20px 0; font-weight:bold; opacity:0.9;">正確な募集要項・期限・申請方法は公式サイトへ</p>
        <a href="{item['link']}" target="_blank" style="display:block; background:#fff; color:#1a73e8; padding:20px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:1.1rem; box-shadow:0 10px 20px rgba(0,0,0,0.1);">J-Net21で一次資料を確認する</a>
    </div>
    <p style="font-size:0.7rem; color:#90949c; margin-top:25px; text-align:center;">出典元：{SOURCE_NAME}</p>
</body></html>"""
    with open(file_path, "w", encoding="utf-8") as f: f.write(html)
    return file_path

def generate_html(subsidies):
    cleanup_old_files()
    list_items = ""
    for i, item in enumerate(subsidies):
        info = ai_analyze(item['title'])
        file_id = hashlib.md5(item['title'].encode()).hexdigest()[:12] + f"_{i}"
        page_path = generate_individual_page(item, info, file_id)
        
        list_items += f"""
        <article style="border:1px solid #dddfe2; padding:25px; margin-bottom:20px; border-radius:12px; background:#fff;">
            <div style="font-size:0.75rem; color:#1a73e8; font-weight:bold; margin-bottom:10px;">{info['cat']} ／ {info['target']}</div>
            <h2 style="font-size:1.1rem; margin:0 0 20px 0; color:#1c1e21; line-height:1.5;">{item['title']}</h2>
            <div style="display:flex; gap:15px;">
                <a href="{page_path}" style="flex:1; text-align:center; background:#f0f2f5; color:#4b4f56; padding:14px; text-decoration:none; border-radius:8px; font-size:0.85rem; font-weight:bold;">詳細解析を確認</a>
                <a href="{item['link']}" target="_blank" style="flex:1; text-align:center; background:#1a73e8; color:#fff; padding:14px; text-decoration:none; border-radius:8px; font-size:0.85rem; font-weight:bold;">公式サイトへ</a>
            </div>
        </article>"""
    
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AI補助金ナビ</title></head>
<body style="max-width:600px; margin:0 auto; background:#f0f2f5; padding:20px; font-family:-apple-system, sans-serif;">
    <header style="margin-bottom:40px; text-align:center; padding-top:20px;">
        <h1 style="margin:0; font-size:1.8rem; color:#1a73e8; font-weight:bold;">AI補助金ナビ</h1>
        <div style="display:inline-block; background:#fa3e3e; color:#fff; font-size:0.8rem; font-weight:bold; padding:5px 15px; border-radius:20px; margin-top:12px;">毎日AM9:00更新。ブックマーク推奨</div>
    </header>
    <main>{list_items}</main>
</body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

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
