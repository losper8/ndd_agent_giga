## Installation

### download model

```bash
pip install huggingface-cli 
huggingface-cli download sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 --local-dir models/paraphrase-multilingual-MiniLM-L12-v2 --local-dir-use-symlinks False
```

### set up telegram bot

create bot in BotFather and set TELEGRAM_BOT_TOKEN in the config/telegram_bot.env file

for webhook use `ngrok http 8093` and set TELEGRAM_BOT_WEBHOOK_URL in the config/telegram_bot.env file

### run docker-compose
```bash
docker compose -f docker-compose.yaml -p autopatent-back up --build telegram-bot rospatent-scraper redis postgres giga-chat embeddings chromadb
```