#базовый образ
FROM python:3.12-slim 

# рабочая директория
WORKDIR /app 

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

ENV DB_PATH=/data/rental.db
VOLUME ["/data"] #ожидание данных
#порт приложения
EXPOSE 5000 

CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "run:app"]
