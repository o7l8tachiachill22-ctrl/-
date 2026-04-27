# Gemini + Money Forward ME Integration

Google Gemini API とマネーフォワードMEを連携したPythonクライアントです。

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
# .env に GEMINI_API_KEY、MF_EMAIL、MF_PASSWORD を設定してください
```

## 使い方

### 1回限りのプロンプト

```bash
GEMINI_API_KEY=your_key python main.py "日本の首都はどこですか？"
```

### ストリーミング

```bash
python main.py --stream "Pythonについて教えてください"
```

### インタラクティブチャット

```bash
python main.py --interactive
```

### モデル指定

```bash
python main.py --model gemini-1.5-pro "詳しく説明してください"
```

### 利用可能モデル一覧

```bash
python main.py --list-models
```

## モジュールとして使う

```python
import gemini_client

gemini_client.configure()  # GEMINI_API_KEY 環境変数から読み込み

# シンプルなチャット
response = gemini_client.chat("こんにちは！")
print(response)

# ストリーミング
for chunk in gemini_client.stream_chat("長い話をして"):
    print(chunk, end="", flush=True)
```

## マネーフォワードME 連携

`.env` に `MF_EMAIL` と `MF_PASSWORD` を設定した上で以下のコマンドが使えます。

### 資産残高の確認

```bash
python main.py --mf-assets
```

### 最近の取引一覧

```bash
python main.py --mf-transactions
```

### Gemini による家計分析

```bash
python main.py --mf-analyze
# ストリーミング出力
python main.py --mf-analyze --stream
```

### モジュールとして使う

```python
from moneyforward_client import MoneyForwardClient

client = MoneyForwardClient()  # MF_EMAIL / MF_PASSWORD 環境変数から読み込み
assets = client.get_assets()
print(assets["total_assets"])       # 総資産（円）
print(assets["accounts"])           # 口座別残高リスト

transactions = client.get_transactions()
for tx in transactions:
    print(tx["date"], tx["content"], tx["amount"])
```
