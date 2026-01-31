import os, requests, re, hashlib, glob
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI

SOURCE_NAME = "J-Net21（中小機構）"
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
    """情報の薄さを解消するため、推論ステップを一段階掘り下げたプロンプト"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """補助金タイトルから、以下の項目を論理的に推測・抽出せよ。
1.カテゴリ：[製造・建設, IT・DX, 商業・サービス, その他]から厳選
2.対象者：(例：小規模事業者, 中堅企業など)
3.活用例：(この補助金で何ができるか15文字以内)
4.概算金額：(金額が不明なら'自治体HP参照'と記載)
5.推奨度：(★1-5)
形式：カテゴリ/対象者/活用例/概算金額/推奨度"""},
                {"role": "user", "content": title}
            ]
        )
        res = response.choices[0].message.content.split("/")
        return res[0], res[1], res[2], res[3], res[4]
    except: return "その他", "要資料確認", "公式ページを参照", "自治体HP参照", "★★★"

def generate_individual_page(item, cat, target, usage, amount, score, file_id):
    file_path = f"articles/{file_id}.html"
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['title']}</title></head>
<body style="max-width:600px; margin:0 auto; padding:40px 20px; font-family:sans-serif; line-height:1.6; color:#333; background:#f9f9f9;">
    <a href="../index.html" style="color:#1a73e8; text-decoration:none;">← 一覧へ戻る</a>
    <h1 style="font-size:1.3rem; margin:20px 0; border-left:4px solid #1a73e8; padding-left:15px;">{item['title']}</h1>
    <div style="background:#fff; padding:20px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05); margin-bottom:20px;">
        <table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
            <tr style="border-bottom:1px solid #eee;"><td style="padding:10px; color:#666; width:30%;">カテゴリ</td><td style="padding:10px; font-weight:bold;">{cat}</td></tr>
            <tr style="border-bottom:1px solid #eee;"><td style="padding:10px; color:#666;">対象者</td><td style="padding:10px; font-weight:bold;">{target}</td></tr>
            <tr style="border-bottom:1px solid #eee;"><td style="padding:10px; color:#666;">活用イメージ</td><td style="padding:10px; font-weight:bold;">{usage}</td></tr>
            <tr style="border-bottom:1px solid #eee;"><td style="padding:10px; color:#666;">概算金額</td><td style="padding:10px; font-weight:bold; color:#e65100;">{amount}</td></tr>
            <tr><td style="padding:10px; color:#666;">推奨度</td><td style="padding:10px; font-weight:bold; color:#fbc02d;">{score}</td></tr>
        </table>
    </div>
    <div style="margin-top:30px; text-align:center;">
        <p style="font-size:0.8rem; color:#666; margin-bottom:15px;">※上記はタイトルからのAI推測です。詳細は必ず以下よりご確認ください。</p>
        <a href="{item['link']}" target="_blank" style="display:block; background:#0d47a1; color:#fff; padding:18px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:1.1rem;">公式サイト(J-Net21)で一次資料を見る</a>
    </div>
</body></html>"""
    with open(file_path, "w", encoding="utf-8") as f: f.write(html)
    return file_path

def generate_html(subsidies):
    cleanup_old_files()
    list_items = ""
    article_urls = []
    for i, item in enumerate(subsidies):
        cat, target, usage, amount, score = ai_analyze(item['title'])
        file_id = hashlib.md5(item['title'].encode()).hexdigest()[:12] + f"_{i}"
        page_path = generate_individual_page(item, cat, target, usage, amount, score, file_id)
        article_urls.append(page_path)
        
        list_items += f"""
        <article style="border:1px solid #e0e0e0; padding:20px; margin-bottom:15px; border-radius:10px; background:#fff;">
            <div style="font-size:0.65rem; color:#1a73e8; font-weight:bold; margin-bottom:5px;">{cat} | {target}</div>
            <h2 style="font-size:1rem; margin:0 0 15px 0; color:#202124; line-height:1.4;">{item['title']}</h2>
            <div style="display:flex; gap:10px;">
                <a href="{page_path}" style="flex:1; text-align:center; background:#f8f9fa; border:1px solid #dadce0; color:#3c4043; padding:10px; text-decoration:none; border-radius:6px; font-size:0.8rem; font-weight:bold;">クイック確認</a>
                <a href="{item['link']}" target="_blank" style="flex:1; text-align:center; background:#1a73e8; color:#fff; padding:10px; text-decoration:none; border-radius:6px; font-size:0.8rem; font-weight:bold;">公式サイト</a>
            </div>
        </article>"""
    
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI補助金ナビ</title></head>
<body style="max-width:600px; margin:0 auto; background:#f1f3f4; padding:20px; font-family:sans-serif;">
    <header style="margin-bottom:25px;">
        <h1 style="margin:0; font-size:1.5rem;">AI補助金ナビ</h1>
        <p style="font-size:0.8rem; color:#d32f2f; font-weight:bold; margin:5px 0;">📍 毎日AM9:00更新。ブックマークしてご活用ください。</p>
    </header>
    <main>{list_items}</main>
</body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
    # Sitemap生成省略（ロジックは前回同様）
