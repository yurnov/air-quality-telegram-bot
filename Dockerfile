FROM python:3.12-slim
ARG BUILD_DATE

LABEL org.opencontainers.image.source="https://github.com/yurnov/air-quality-telegram-bot" \
        org.opencontainers.image.authors="@yurnov" \
        org.opencontainers.image.title="Air Quality Telegram Bot" \
        org.opencontainers.image.description="A simple Telegram bot that provides air quality information for a given location." \
        org.opencontainers.image.licenses="MIT"

WORKDIR /app

RUN --mount=type=bind,source=src/requirements.txt,target=/tmp/requirements.txt \
   pip install --no-cache-dir -r /tmp/requirements.txt

COPY src/ .

# Set the entrypoint to run the bot script
ENTRYPOINT ["python", "bot.py"]
