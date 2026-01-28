import os
import requests
import xml.etree.ElementTree as ET # 標準ライブラリで完結
from datetime import datetime

def run_scraper():
    AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
    AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
    AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
    
    # 作用機序: スクレイピング遮断を回避するため、公式のRSSフィード(XML)を叩く
    RSS_URL = "https://j-net21.smrj.go.jp/snavi/support/rss.xml"
    
    try:
        print(f"DEBUG: 公式RSSフィード ({RSS_URL}) を取得中...")
        res = requests.get(RSS_URL, timeout=20)
        res.encoding = 'utf-8'
        
        # XMLの解析
        root = ET.fromstring(res.text)
        records = []
        
        # RSS(XML)の構造: <item>タグの中に情報が入っている
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text
            link = item.find('link').text
            
            records.append({
                "fields": {
                    "title": title,
                    "region": "新着（公式配信）",
                    "source_url": link
                }
            })

        if not records:
            print("【失敗】RSSからもデータが取得できませんでした。")
            return

        # Airtableへの送信
        airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}
        response = requests.post(airtable_url, headers=headers, json={"records": records})
        
        print(f"DEBUG: 送信成功 - ステータスコード {response.status_code}")
        
    except Exception as e:
        print(f"【致命的エラー】: {e}")

if __name__ == "__main__":
    run_scraper()
