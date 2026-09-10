FROM docker.m.daocloud.io/library/python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py api.py platform_data.py ./

EXPOSE 8501 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
