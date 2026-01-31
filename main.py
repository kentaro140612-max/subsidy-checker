import os, hashlib, json, re, requests
from bs4 import BeautifulSoup
from openai import OpenAI

# 構成設定
SOURCE_NAME = "J-Net21"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def ai_analyze_minimal(title):
    """
    推論を極限まで単純化。バッジの『テキスト』のみを生成させる。
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": '{"cat":"IT/製造/商業/他", "size":"大規模/中規模/少額"}'},
                {"role": "user", "content": title}
            ]
        )
        d = json.loads(response.choices[0].message.content)
        return f"【{d.get('cat', '他')}】", f"[{d.get('size', '確認')}]"
    except:
        return "【他】", "[確認]"

def fetch_all_new_data():
    """取得件数を物理的に増やし、網羅性を担保する"""
    url = "https://j-net21.smrj.go.jp/snavi/articles"
    res = requests.get(url, timeout=30)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    links = soup.find_all('a', href=re.compile(r'/snavi/articles/\d+'))
    
    unique_data = []
    seen = set()
    for a in links:
        t = a.get_text(strip=True)
        if len(t) > 10 and t not in seen:
            h = a.get('href')
            full_url = h if h.startswith('http') else "https://j-net21.smrj.go.jp" + h
            unique_data.append({"title": t, "link": full_url})
            seen.add(t)
            if len(unique_data) >= 30: break # 30件まで拡張
    return unique_data

def generate_html(subsidies):
    list_items = ""
    for item in subsidies:
        cat_tag, size_tag = ai_analyze_minimal(item['title'])
        
        # 色に頼らず、テキストの太字と記号だけで情報を識別させる
        list_items += f"""
        <article style="border-bottom:1px solid #e1e4e8; padding:20px 0; background:#ffffff;">
            <div style="font-size:0.8rem; font-weight:bold; color:#2b6cb0; margin-bottom:8px;">
                {cat_tag} {size_tag}
            </div>
            <h2 style="font-size:1rem; margin:0 0 15px 0; color:#1a1a1a; line-height:1.5;">{item['title']}</h2>
            <a href="{item['link']}" target="_blank" style="display:inline-block; border:2px solid #2b6cb0; color:#2b6cb0; padding:10px 20px; text-decoration:none; border-radius:6px; font-size:0.85rem; font-weight:bold;">公式サイトを確認</a>
        </article>"""
    
    html_content = f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>補助金DB</title></head>
<body style="max-width:600px; margin:0 auto; background:#ffffff; padding:20px; font-family:sans-serif; color:#1a1a1a;">
    <header style="border-bottom:3px solid #1a1a1a; padding-bottom:10px; margin-bottom:30px;">
        <h1 style="font-size:1.5rem; margin:0;">AI補助金ナビ 2.0</h1>
        <p style="font-size:0.8rem; color:#666;">J-Net21最新30件をAIが自動分類</p>
    </header>
    <main>{list_items}</main>
</body></html>"""
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)

if __name__ == "__main__":
    subsidies = fetch_all_new_data()
    if subsidies: generate_html(subsidies)
