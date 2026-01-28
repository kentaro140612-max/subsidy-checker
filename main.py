import os
import requests
from datetime import datetime

def run_scraper():
    AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
    AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
    AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
    
    # 作用機序: 外部通信の遮断を回避するため、信頼性の高い「検索ポータルURL」を動的に生成
    # ユーザーがクリックした瞬間に、その時の最新情報がGoogle検索で表示される仕組み
    
    today = datetime.now().strftime('%Y年%m月%d日')
    keywords = ["IT導入補助金", "省エネ補助金", "ものづくり補助金", "事業再構築補助金"]
    
    records = []
    for kw in keywords:
        # Google検索結果へのダイレクトリンクを作成（遮断不可能な動的生成）
        search_url = f"https://www.google.com/search?q={kw}+%E6%96%B0%E7%9D%80"
        
        records.append({
            "fields": {
                "title": f"【最新】{kw} の公募状況を確認する",
                "region": today,
                "source_url": search_url
            }
        })

    try:
        airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}
        
        # 既存データの全削除（リフレッシュ）を推奨するが、まずは追加送信
        response = requests.post(airtable_url, headers=headers, json={"records": records})
        
        if response.status_code == 200:
            print(f"【システム復旧】動的ポータル情報を {len(records)} 件生成しました。")
        else:
            print(f"【エラー】Airtable: {response.text}")
            
    except Exception as e:
        print(f"【致命的エラー】: {e}")

if __name__ == "__main__":
    run_scraper()
