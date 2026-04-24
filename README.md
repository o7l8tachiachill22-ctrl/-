# Gemini Integration

Google Gemini API を使ったシンプルなPythonクライアントです。

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
# .env に GEMINI_API_KEY を設定してください
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
