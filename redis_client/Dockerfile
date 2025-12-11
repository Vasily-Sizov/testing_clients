FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY test_app/requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь модуль (кроме test_app)
COPY client/ ./client/
COPY __init__.py ./
COPY lifespan.py ./
COPY routes.py ./
COPY entities.py ./

# Копируем код тестового приложения
COPY test_app/main.py ./main.py

# Запускаем приложение
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

