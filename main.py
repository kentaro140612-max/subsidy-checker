import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from supabase import create_client

# [環境変数の読み込み] 
# GitHub Secretsから安全に情報を取得します
try:
    openai_key = os.environ["OPENAI_API_KEY"]
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_KEY"]
except KeyError as e:
    print(f"Error: Environment variable {e} not set.")
    exit(1)

# クライアントの初期化
client = OpenAI(api_key=openai_key)
supabase = create_client(supabase_url, supabase_key)

def get_latest_subsidies():
    # J-Net21の補助金新着ページ（例）
    url = "https://j-net21.smrj.go.jp/snavi/articles"
    res = requests.get(url)
    res.encoding = res.apparent_encoding # 文字化け防止
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 記事タイトルを取得（最新3件）
    articles = soup.select('h3')[:3] 
    for art in articles:
        title = art.get_text(strip=True)
        print(f"確認されたタイトル: {title}")
        # 次のステップでここにAI解析とDB保存のロジックを統合します

if __name__ == "__main__":
    get_latest_subsidies()
