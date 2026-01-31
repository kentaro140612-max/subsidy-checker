import os, hashlib, json, re
from openai import OpenAI

# 構成設定
SOURCE_NAME = "J-Net21（中小機構）"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
os.makedirs("articles", exist_ok=True)

def get_badge_logic(amount_str, category):
    """
    AIの出力を介さず、Python側で物理的に色とアイコンを決定する。
    """
    # 1. アイコンの決定
    icon_map = {"IT・DX": "💻", "製造・建設": "🏗️", "商業・サービス": "🛍️", "その他": "💡"}
    icon = icon_map.get(category, "💡")

    # 2. 色の決定（キーワードによる物理判定）
    # 大規模：500万以上、拠点、大規模
    if any(k in amount_str for k in ["500", "1000", "5000", "億", "大規模", "拠点"]):
        return icon, "大規模支援", "#6b46c1" # 紫
    # 中規模：100万以上
    elif any(k in amount_str for k in ["100", "200", "300", "400", "中規模"]):
        return icon, "中規模支援", "#2b6cb0" # 青
    # 少額：それ以外
    else:
        return icon, "少額支援", "#2f855a" # 緑

def ai_analyze(title):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": '{"cat":"製造・建設 or IT・DX or 商業・サービス or その他", "target":"対象者", "usage":"内容", "amount":"〜〇〇万円", "score":1-5}'},
                {"role": "user", "content": title}
            ]
        )
        d = json.loads(response.choices[0].message.content)
        s = int(d.get("score", 3))
        return d.get("cat"), d.get("target"), d.get("usage"), d.get("amount"), '★'*s + '☆'*(5-s)
    except:
        return "その他", "事業者", "詳細確認", "10万円〜", "★★★☆☆"

def generate_individual_page(item, cat, target, usage, amount, score, file_id):
    file_path = f"articles/{file_id}.html"
    icon, b_name, b_color = get_badge_logic(amount, cat)
    
    html = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>{item['title']}</title></head>
<body style="max-width:600px; margin:0 auto; padding:30px 20px; font-family:sans-serif; background:#f7fafc; color:#1a202c;">
    <a href="../index.html" style="color:#2b6cb0; text-decoration:none; font-weight:bold;">← 戻る</a>
    <div style="margin:20px 0;">
        <span style="background-color:{b_color} !important; color:#ffffff !important; padding:6px 14px; border-radius:6px; font-weight:bold; font-size:0.8rem; display:inline-block;">{icon} {b_name}</span>
    </div>
    <h1 style="font-size:1.25rem; line-height:1.4; margin-bottom:25px;">{item['title']}</h1>
    <div style="background:#ffffff; padding:25px; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.05); border:1px solid #e2e8f0;">
        <table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
            <tr style="border-bottom:1px solid #edf2f7;"><td style="padding:12px 0; color:#718096; width:40%;">対象者</td><td style="font-weight:bold;">{target}</td></tr>
            <tr style="border-bottom:1px solid #edf2f7;"><td style="padding:12px 0; color:#718096;">活用内容</td><td style="font-weight:bold;">{usage}</td></tr>
            <tr style="border-bottom:1px solid #edf2f7;"><td style="padding:12px 0; color:#718096;">推定金額</td><td style="font-weight:bold; color:#c53030;">{amount}</td></tr>
            <tr><td style="padding:12px 0; color:#718096;">おすすめ度</td><td style="font-weight:bold; color:#d69e2e; letter-spacing:2px;">{score}</td></tr>
        </table>
    </div>
    <div style="margin-top:30px; background:#2b6cb0; padding:30px; border-radius:10px; text-align:center;">
        <a href="{item['link']}" target="_blank" style="display:block; background:#ffffff; color:#2b6cb0; padding:15px; text-decoration:none; border-radius:6px; font-weight:bold;">公式サイトで確認する</a>
    </div>
</body></html>"""
    with open(file_path, "w", encoding="utf-8") as f: f.write(html)
    return file_path

def generate_html(subsidies):
    list_items = ""
    for i, item in enumerate(subsidies):
        cat, target, usage, amount, score = ai_analyze(item['title'])
        file_id = hashlib.md5(item['title'].encode()).hexdigest()[:12] + f"_{i}"
        path = generate_individual_page(item, cat, target, usage, amount, score, file_id)
        icon, b_name, b_color = get_badge_logic(amount, cat)
        
        list_items += f"""
        <article style="border:1px solid #e2e8f0; padding:20px; margin-bottom:15px; border-radius:12px; background:#ffffff;">
            <div style="display:flex; justify-content:space-between; margin-bottom:12px; align-items:center;">
                <span style="font-size:0.7rem; font-weight:bold; color:#2b6cb0;">{icon} {cat}</span>
                <span style="background-color:{b_color} !important; color:#ffffff !important; font-size:0.65rem; padding:3px 10px; border-radius:4px; font-weight:bold; display:inline-block;">{b_name}</span>
            </div>
            <h2 style="font-size:1rem; margin:0 0 15px 0; color:#2d3748; line-height:1.5;">{item['title']}</h2>
            <div style="display:flex; gap:10px;">
                <a href="{path}" style="flex:1; text-align:center; background:#edf2f7; color:#4a5568; padding:10px; text-decoration:none; border-radius:6px; font-size:0.8rem; font-weight:bold;">解析を確認</a>
                <a href="{item['link']}" target="_blank" style="flex:1; text-align:center; background:#2b6cb0; color:#ffffff; padding:10px; text-decoration:none; border-radius:6px; font-size:0.8rem; font-weight:bold;">公式サイト</a>
            </div>
        </article>"""
    
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>AI補助金ナビ</title></head>
<body style="max-width:600px; margin:0 auto; background:#f7fafc; padding:20px; font-family:sans-serif;">
    <header style="margin-bottom:30px; text-align:center;">
        <h1 style="color:#2b6cb0; font-size:1.6rem; margin:0;">AI補助金ナビ</h1>
        <div style="background:#e53e3e; color:#ffffff; font-size:0.75rem; font-weight:bold; padding:4px 12px; border-radius:20px; display:inline-block; margin-top:8px;">毎日更新</div>
    </header>
    <main>{list_items}</main>
</body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
