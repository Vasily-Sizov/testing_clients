FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY test_app/requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь модуль my_artemis_client
COPY my_artemis_client/ ./my_artemis_client/

# Копируем код тестового приложения
COPY test_app/ ./test_app/

# Запускаем приложение
CMD ["uvicorn", "test_app.main:app", "--host", "0.0.0.0", "--port", "8000"]

