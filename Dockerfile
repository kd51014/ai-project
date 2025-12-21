FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

# domyślnie uruchamia Flask dev server
CMD ["python", "run.py"]
