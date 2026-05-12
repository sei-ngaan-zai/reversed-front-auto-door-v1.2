FROM python:3.9.16-slim

WORKDIR /app

# Install setuptools first to fix pkg_resources issue
RUN pip install setuptools==44.0.0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "main:app"]

