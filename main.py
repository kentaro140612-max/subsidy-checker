import os, requests, re, hashlib, glob, json
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI

SOURCE_NAME = "J-Net21（独立行政法人 中小企業基盤整備機構）"
SOURCE_URL = "https://j-net21.smrj.go.jp/"
now_dt = datetime.now()
now = now_dt.strftime('%Y年%m月%d日 %H:%M')
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

os.makedirs("articles", exist_ok=True)

def get_badge_info(amount_str):
    """金額文字列から規模を論理的に判定しバッジ情報を返す"""
    # 数値を抽出して規模を判定
    nums = re.findall(r'\d+', amount_str.replace(',', ''))
    val = int(nums[0]) if nums else 0
    
    if val >= 500: return "大規模", "#6b46c1" # 紫
    if val >= 100: return "中規模", "#2b6cb0" # 青
    return "少額支援", "#2f855a" # 緑

def ai_analyze(title):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": """補助金タイトルを分析しJSONで返せ。
項目: category(製造・建設, IT・DX, 商業・サービス, その他), target(対象者), usage(支援対象となる活動), amount(金額感:数値を含む具体的な文字列), score(1-5)"""},
                {"role": "user", "content": title}
            ]
        )
        data = json.loads(response.choices[0].message.content)
        raw_score = int(data.get("score", 3))
        score_val = max(1, min(5, raw_score))
        return {
            "cat": data.get("category", "その他"),
            "target": data.get("target", "事業者"),
            "usage": data.get("usage", "詳細を確認"),
            "amount": data.get("amount", "10万円〜"),
            "score": '★' * score_val + '☆' * (5 - score_val)
        }
    except:
        return {"cat": "その他", "target": "要確認", "usage": "詳細を確認", "amount": "10万円〜", "score": "★★★☆☆"}

def generate_individual_page(item, info, file_id):
    file_path = f"articles/{file_id}.html"
    badge_name, badge_color = get_badge_info(info['amount'])
    
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['title']}</title></head>
<body style="max-width:600px; margin:0 auto; padding:40px 20px; font-family:sans-serif; line-height:1.6; color:#1a202c; background:#f7fafc;">
    <a href="../index.html" style="color:#2b6cb0; text-decoration:none; font-weight:bold; font-size:0.9rem;">← 一覧に戻る</a>
    <div style="margin:20px 0;">
        <span style="background:{badge_color}; color:#fff; font-size:0.75rem; padding:4px 12px; border-radius:4px; font-weight:bold;">{badge_name}</span>
    </div>
    <h1 style="font-size:1.4rem; margin:0 0 25px 0; color:#2d3748; line-height:1.4;">{item['title']}</h1>
    
    <div style="background:#fff; padding:30px; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:30px; border:1px solid #e2e8f0;">
        <table style="width:100%; border-collapse:collapse; font-size:0.95rem;">
            <tr style="border-bottom:1px solid #edf2f7;"><td style="padding:15px 0; color:#718096; width:45%;">カテゴリ</td><td style="padding:15px 0; font-weight:bold;">{info['cat']}</td></tr>
            <tr style="border-bottom:1px solid #edf2f7;"><td style="padding:15px 0; color:#718096;">主な対象者</td><td style="padding:15px 0; font-weight:bold;">{info['target']}</td></tr>
            <tr style="border-bottom:1px solid #edf2f7;"><td style="padding:15px 0; color:#718096;">支援対象となる活動</td><td style="padding:15px 0; font-weight:bold;">{info['usage']}</td></tr>
            <tr style="border-bottom:1px solid #edf2f7;"><td style="padding:15px 0; color:#718096;">推定補助金額</td><td style="padding:15px 0; font-weight:bold; color:#c53030;">{info['amount']}</td></tr>
            <tr><td style="padding:15px 0; color:#718096;">AIおすすめ度</td><td style="padding:15px 0; font-weight:bold; color:#d69e2e; letter-spacing:2px; font-family:monospace;">{info['score']}</td></tr>
        </table>
    </div>

    <div style="background:#2b6cb0; padding:35px; border-radius:12px; text-align:center;">
        <a href="{item['link']}" target="_blank" style="display:block; background:#fff; color:#2b6cb0; padding:18px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:1.1rem; box-shadow:0 4px 6px rgba(0,0,0,0.1);">公式サイトで一次資料を確認</a>
    </div>
    <p style="font-size:0.7rem; color:#a0aec0; margin-top:25px; text-align:center;">出典元：{SOURCE_NAME}</p>
</body></html>"""
    with open(file_path, "w", encoding="utf-8") as f: f.write(html)
    return file_path

def generate_html(subsidies):
    list_items = ""
    for i, item in enumerate(subsidies):
        info = ai_analyze(item['title'])
        file_id = hashlib.md5(item['title'].encode()).hexdigest()[:12] + f"_{i}"
        page_path = generate_individual_page(item, info, file_id)
        badge_name, badge_color = get_badge_info(info['amount'])
        
        list_items += f"""
        <article style="border:1px solid #e2e8f0; padding:25px; margin-bottom:20px; border-radius:16px; background:#fff;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <span style="font-size:0.7rem; color:#2b6cb0; font-weight:bold;">{info['cat']} ／ {info['target']}</span>
                <span style="background:{badge_color}; color:#fff; font-size:0.65rem; padding:2px 8px; border-radius:4px; font-weight:bold;">{badge_name}</span>
            </div>
            <h2 style="font-size:1.05rem; margin:0 0 20px 0; color:#2d3748; line-height:1.5;">{item['title']}</h2>
            <div style="display:flex; gap:12px;">
                <a href="{page_path}" style="flex:1; text-align:center; background:#edf2f7; color:#4a5568; padding:12px; text-decoration:none; border-radius:8px; font-size:0.85rem; font-weight:bold;">詳細を確認</a>
                <a href="{item['link']}" target="_blank" style="flex:1; text-align:center; background:#2b6cb0; color:#fff; padding:12px; text-decoration:none; border-radius:8px; font-size:0.85rem; font-weight:bold;">公式サイト</a>
            </div>
        </article>"""
    
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AI補助金ナビ</title></head>
<body style="max-width:600px; margin:0 auto; background:#f7fafc; padding:20px; font-family:sans-serif;">
    <header style="margin-bottom:40px; text-align:center;">
        <h1 style="margin:0; font-size:1.8rem; color:#2b6cb0; font-weight:bold;">AI補助金ナビ</h1>
        <div style="display:inline-block; background:#e53e3e; color:#fff; font-size:0.8rem; font-weight:bold; padding:5px 15px; border-radius:20px; margin-top:12px;">毎日AM9:00更新。ブックマーク推奨</div>
    </header>
    <main>{list_items}</main>
</body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
