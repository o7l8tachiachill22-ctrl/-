# Gemini Integration + チャッピー (ChatGPT) Integration

Google Gemini API および OpenAI ChatGPT (チャッピー) を使ったシンプルなPythonクライアントです。

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
# .env に GEMINI_API_KEY と OPENAI_API_KEY を設定してください
```

## 使い方 — Gemini

### 1回限りのプロンプト

```bash
python main.py "日本の首都はどこですか？"
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

## 使い方 — チャッピー (ChatGPT)

`--chappy` フラグを付けると OpenAI ChatGPT を使います。

### 1回限りのプロンプト

```bash
python main.py --chappy "日本の首都はどこですか？"
```

### ストリーミング

```bash
python main.py --chappy --stream "Pythonについて教えてください"
```

### インタラクティブチャット

```bash
python main.py --chappy --interactive
```

### モデル指定（例: GPT-4o）

```bash
python main.py --chappy --model gpt-4o "詳しく説明してください"
```

### 利用可能モデル一覧

```bash
python main.py --chappy --list-models
```

## モジュールとして使う

```python
import gemini_client
import chappy_client

# --- Gemini ---
gemini_client.configure()  # GEMINI_API_KEY 環境変数から読み込み
response = gemini_client.chat("こんにちは！")
print(response)

# --- チャッピー (ChatGPT) ---
chappy_client.configure()  # OPENAI_API_KEY 環境変数から読み込み
response = chappy_client.chat("こんにちは！")
print(response)

# ストリーミング
for chunk in chappy_client.stream_chat("長い話をして"):
    print(chunk, end="", flush=True)
```
