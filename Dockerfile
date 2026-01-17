FROM python:3.11-slim

WORKDIR /app

# playwright 설치가 오래 걸리므로 먼저 설치해 캐시 활용
RUN apt-get update && \
    pip install playwright && \
    playwright install chromium && \
    playwright install-deps chromium && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
