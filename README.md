## Installation

### download model

```bash
pip install huggingface-cli 
huggingface-cli download sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 --local-dir models/paraphrase-multilingual-MiniLM-L12-v2 --local-dir-use-symlinks False
```

### set up telegram bot

create bot in BotFather and set TELEGRAM_BOT_TOKEN in the config/telegram_bot.env file

for webhook use `ngrok http 8083` and set TELEGRAM_BOT_WEBHOOK_URL in the config/telegram_bot.env file

### run docker-compose
UPDATED
```bash
docker compose --env-file config/postgres.env -f docker-compose.yaml -p autopatent-back up --build autopatent-clusters autopatent-embeddings autopatent-giga-chat autopatent-rospatent-scraper autopatent-telegram-bot autopatent-postgres chromadb redis keycloak
```

### Для кейклока
Если у postgresl в логах 

```
PostgreSQL Database directory appears to contain a database; Skipping initialization
```
Означает что старая бд уже есть и скрипт инициализации не запустился
Нужно внутри контейнера postgresql

```bash
bash docker-entrypoint-initdb.d/db-init.sh
```
