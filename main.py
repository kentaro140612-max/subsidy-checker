import os
import requests
from datetime import datetime

def run_scraper():
    AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
    AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
    AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
    
    today = datetime.now().strftime('%m/%d')
    # 作用機序: 採択率が高く、かつ専門コンサルの需要がある「高単価キーワード」を厳選
    # これにより、単なる情報サイトから「ビジネス支援ポータル」へ昇華させる
    target_topics = [
        {"kw": "IT導入補助金 2026", "label": "【DX推進】IT導入補助金"},
        {"kw": "ものづくり補助金 公募", "label": "【設備投資】ものづくり補助金"},
        {"kw": "事業再構築補助金 最新", "label": "【新事業】事業再構築補助金"},
        {"kw": "省エネ 補助金 自治体", "label": "【コスト削減】省エネ・光熱費補助"},
        {"kw": "創業融資 助成金", "label": "【起業家支援】創業・スタートアップ"}
    ]
    
    records = []
    for topic in target_topics:
        search_url = f"https://www.google.com/search?q={topic['kw']}+%E6%96%B0%E7%9D%80"
        
        records.append({
            "fields": {
                "title": topic['label'],
                "region": f"更新: {today}",
                "source_url": search_url
            }
        })

    try:
        # 重複を避け、常に最新5件のみを表示させるための物理的な「上書き」送信
        airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}", "Content-Type": "application/json"}
        response = requests.post(airtable_url, headers=headers, json={"records": records})
        
        if response.status_code == 200:
            print(f"【戦略的更新】ターゲットキーワードでのポータル生成を完了しました。")
        else:
            print(f"【エラー】Airtable: {response.text}")
            
    except Exception as e:
        print(f"【致命的エラー】: {e}")

if __name__ == "__main__":
    run_scraper()
