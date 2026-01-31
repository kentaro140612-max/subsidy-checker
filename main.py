import os, requests, re, hashlib, glob
from bs4 import BeautifulSoup
from datetime import datetime
from openai import OpenAI

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

def normalize_score(score_str):
    """スコア表記を『★★★☆☆』の形式に統一する"""
    count = score_str.count('★')
    if count == 0: count = 3 # デフォルト
    return '★' * count + '☆' * (5 - count)

def ai_analyze(title):
    """推論を極限まで強制し、表記の揺れを最小化する"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """補助金タイトルから支援規模を推論せよ。
【ルール】
1.金額感:必ず「〜50万円」「100万円〜」等の数値を出す。'参照'は厳禁。
2.カテゴリ:製造・建設, IT・DX, 商業・サービス, その他 から選択。
3.形式:カテゴリ/対象者/活動内容/金額感/星数(1-5)"""},
                {"role": "user", "content": title}
            ]
        )
        res = response.choices[0].message.content.split("/")
        while len(res) < 5: res.append("3")
        return res[0], res[1], res[2], res[3], normalize_score(res[4])
    except:
        return "その他", "中小企業・個人事業主", "公式資料を確認", "10万円〜(推計)", "★★★☆☆"

def generate_individual_page(item, cat, target, usage, amount, score, file_id):
    file_path = f"articles/{file_id}.html"
    # 金額の表記ガードレール
    display_amount = amount if any(c.isdigit() for c in amount) else "10万円〜(自治体規模による)"
    
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['title']}</title></head>
<body style="max-width:600px; margin:0 auto; padding:40px 20px; font-family:sans-serif; line-height:1.6; color:#333; background:#f4f7f9;">
    <a href="../index.html" style="color:#1a73e8; text-decoration:none; font-size:0.9rem;">← 一覧に戻る</a>
    <h1 style="font-size:1.4rem; margin:20px 0; color:#202124; line-height:1.4;">{item['title']}</h1>
    
    <div style="background:#fff; padding:25px; border-radius:15px; box-shadow:0 10px 25px rgba(0,0,0,0.05); margin-bottom:30px; border:1px solid #e0e6ed;">
        <h3 style="margin:0 0 20px 0; font-size:1rem; color:#1a73e8;">🔍 AI解析レポート</h3>
        <table style="width:100%; border-collapse:collapse; font-size:0.95rem;">
            <tr style="border-bottom:1px solid #f0f4f8;"><td style="padding:15px 0; color:#6b7280; width:45%;">カテゴリ</td><td style="padding:15px 0; font-weight:bold;">{cat}</td></tr>
            <tr style="border-bottom:1px solid #f0f4f8;"><td style="padding:15px 0; color:#6b7280;">対象ターゲット</td><td style="padding:15px 0; font-weight:bold;">{target}</td></tr>
            <tr style="border-bottom:1px solid #f0f4f8;"><td style="padding:15px 0; color:#6b7280;">支援対象となる活動</td><td style="padding:15px 0; font-weight:bold;">{usage}</td></tr>
            <tr style="border-bottom:1px solid #f0f4f8;"><td style="padding:15px 0; color:#6b7280;">推定補助金額</td><td style="padding:15px 0; font-weight:bold; color:#d32f2f; font-size:1.1rem;">{display_amount}</td></tr>
            <tr><td style="padding:15px 0; color:#6b7280;">AIおすすめ度</td><td style="padding:15px 0; font-weight:bold; color:#f59e0b; font-size:1.1rem; letter-spacing:2px;">{score}</td></tr>
        </table>
    </div>

    <div style="background:#1a73e8; padding:30px; border-radius:15px; text-align:center;">
        <p style="color:#fff; font-size:0.9rem; margin:0 0 15px 0; opacity:0.9;">正確な募集要項・申請期限は公式サイトへ</p>
        <a href="{item['link']}" target="_blank" style="display:block; background:#fff; color:#1a73e8; padding:18px; text-decoration:none; border-radius:10px; font-weight:bold; font-size:1.1rem; box-shadow:0 4px 10px rgba(0,0,0,0.1);">J-Net21で一次資料を確認する</a>
    </div>
    <p style="font-size:0.75rem; color:#9ca3af; margin-top:25px; text-align:center; line-height:1.4;">※本内容はタイトルからAIが推論した参考情報です。<br>出典元：{SOURCE_NAME}</p>
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
        <article style="border:1px solid #e5e7eb; padding:25px; margin-bottom:20px; border-radius:16px; background:#fff; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
            <div style="font-size:0.7rem; color:#1a73e8; font-weight:bold; margin-bottom:10px;">{cat} ／ {target}</div>
            <h2 style="font-size:1.1rem; margin:0 0 20px 0; color:#111827; line-height:1.5;">{item['title']}</h2>
            <div style="display:flex; gap:12px;">
                <a href="{page_path}" style="flex:1; text-align:center; background:#f3f4f6; color:#374151; padding:14px; text-decoration:none; border-radius:10px; font-size:0.85rem; font-weight:bold; border:1px solid #d1d5db;">詳細解析を確認</a>
                <a href="{item['link']}" target="_blank" style="flex:1; text-align:center; background:#1a73e8; color:#fff; padding:14px; text-decoration:none; border-radius:10px; font-size:0.85rem; font-weight:bold;">公式サイトへ</a>
            </div>
        </article>"""
    
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI補助金ナビ | 公的支援をAIで即座に視覚化</title></head>
<body style="max-width:600px; margin:0 auto; background:#f9fafb; padding:20px; font-family:sans-serif;">
    <header style="margin-bottom:35px; text-align:center;">
        <h1 style="margin:0; font-size:1.8rem; color:#1a73e8;">AI補助金ナビ</h1>
        <div style="display:inline-block; background:#fee2e2; color:#b91c1c; font-size:0.8rem; font-weight:bold; padding:4px 12px; border-radius:20px; margin-top:10px;">毎日AM9:00更新。ブックマーク推奨</div>
    </header>
    <main>{list_items}</main>
</body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
