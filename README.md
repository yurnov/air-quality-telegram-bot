# Telegram Bot for Air Quality Monitoring

This repository contains a Telegram bot that monitors air quality for a specified city and sends alerts when the air quality reaches certain thresholds. The bot is written in Python and runs in a Docker.

## Setup and Run the Bot

### Prerequisites

- Docker
- Air Quality Historical Data Platform API Key
- Telegram Bot and Bot API Key

### Instructions

1. Clone the repository:

   ```sh
   git https://github.com/yurnov/air-quality-telegram-bot.git
   cd air-quality-telegram-bot
   ```

2. Create a `.env` file in the root directory of the project and add the following environment variables:

   ```sh
   API_KEY=your_api_key
   TELEGRAM_BOT_API_KEY=your_telegram_bot_api_key
   CITY=your_city
   LANGUAGE=your_language (optional, default is 'en')
   CHAT_ID=your_chat_id (optional)
   PULL_INTERVAL=your_pull_interval (optional, default is 10, min is 5, max is 60)
   ```

   Please use `.env.example` as example.

3. Build and run the Docker container:

   ```sh
   docker build . -t ghcr.io/yurnov/air-quality-telegram-bot:latest
   docker run -d --env-file .env ghcr.io/yurnov/air-quality-telegram-bot:latest
   ```

or use ready to use image:

   ```sh
   docker pull ghcr.io/yurnov/air-quality-telegram-bot:latest
   docker run -d --env-file .env ghcr.io/yurnov/air-quality-telegram-bot:latest
   ```

## Environment Variables

- `API_KEY`: API key for `api.waqi.info`
- `TELEGRAM_BOT_API_KEY`: API key for the Telegram bot
- `CITY`: City for which the bot will monitor air quality
- `LANGUAGE`: Language for the bot's messages (optional, default is 'en'). Supported languages: English (`en`), Ukrainian (`uk`), Polish (`pl`)
- `CHAT_ID`: Chat ID for sending alerts (optional)
- `PULL_INTERVAL`: Interval in minutes for pulling data from the API (optional, default is 10, min is 5, max is 60)

## Bot Functionality

- The bot pulls data from `api.waqi.info/feed/:city/?token=:token` at the defined pull interval.
- When a user sends any message to the bot, it responds with the air quality index (AQI) gathered on the last pull.
- If `CHAT_ID` is set and the AQI reaches a threshold, the bot sends a message to this chat with predefined messages for supported languages.

## Future Enhancements

- Move messadges to separate JSON file
- Add support for more languages.
- Implement a mechanism to handle multiple users and chats, allowing the bot to serve more users simultaneously.
