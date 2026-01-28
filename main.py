import os
import requests
from datetime import datetime

def run_scraper():
    AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
    AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
    AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
    
    # 作用機序: 特定サイトの解析を避け、Google検索の検索結果（RSS/API的挙動）を利用する
    # 検索キーワード: 「補助金 新着 2026」
    SEARCH_QUERY = "%E8%A3%9C%E5%8A%A9%E9%87%91%20%E6%96%B0%E7%9D%80%202026"
    TARGET_URL = f"https://www.google.com/search?q={SEARCH_QUERY}&num=10"
    
    try:
        print(f"DEBUG: 検索エンジン経由で最新情報をスキャン中...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(TARGET_URL, headers=headers, timeout=20)
        
        # 物理的制約の回避: Googleの検索結果からリンク（/url?q=...）を抽出
        import re
        links = re.findall(r'/url\?q=(https://.*?)(&|")', res.text)
        
        records = []
        seen_urls = set()
        
        for url, _ in links:
            # 広告やGoogle自身のリンクを除外
            if "google.com" in url or "youtube.com" in url:
                continue
            if url in seen_urls:
                continue
                
            # タイトルはURLから推測または固定（200 OKの確認のみ）
            records.append({
                "fields": {
                    "title": f"最新補助金情報 ({datetime.now().strftime('%m/%d')})",
                    "region": "新着検索結果",
                    "source_url": url
                }
            })
            seen_urls.add(url)
            if len(records) >= 5: break

        if not records:
            print("【失敗】検索結果からも抽出できませんでした。プロトコルを変更します。")
            return

        # Airtable送信
        airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}
        response = requests.post(airtable_url, headers=headers, json={"records": records})
        
        if response.status_code == 200:
            print(f"【成功】検索結果から {len(records)} 件のリンクを保存しました。")
        else:
            print(f"【エラー】Airtable: {response.text}")
            
    except Exception as e:
        print(f"【致命的エラー】: {e}")

if __name__ == "__main__":
    run_scraper()
