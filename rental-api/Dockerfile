FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

ENV DB_PATH=/data/rental.db
VOLUME ["/data"]
EXPOSE 5000

CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "run:app"]
