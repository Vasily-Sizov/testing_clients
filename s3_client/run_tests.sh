#!/bin/bash
# Скрипт для запуска тестов с правильными переменными окружения

# Устанавливаем переменные окружения
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin
export AWS_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:9000
export AWS_USE_SSL=false
export AWS_VERIFY=false

# Выводим переменные для отладки (можно закомментировать)
echo "Environment variables:"
echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
echo "AWS_REGION=$AWS_REGION"
echo "AWS_ENDPOINT_URL=$AWS_ENDPOINT_URL"
echo "AWS_USE_SSL=$AWS_USE_SSL"
echo "AWS_VERIFY=$AWS_VERIFY"
echo ""

# Запускаем pytest с переменными окружения
# Используем env для явной передачи переменных
env AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    AWS_REGION="$AWS_REGION" \
    AWS_ENDPOINT_URL="$AWS_ENDPOINT_URL" \
    AWS_USE_SSL="$AWS_USE_SSL" \
    AWS_VERIFY="$AWS_VERIFY" \
    uv run pytest tests/ -m integration -v

