FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# App Platform ignores EXPOSE, but fine to keep
EXPOSE 8080

# PRODUCTION COMMAND
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4
