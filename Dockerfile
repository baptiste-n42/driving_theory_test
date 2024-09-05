FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install -U .

VOLUME ["/app/configuration.ini"]

HEALTHCHECK --interval=5m --timeout=3s \
              CMD curl -f http://localhost:8000/healthcheck1 || exit 1

CMD ["gunicorn", "driving_theory_test:create_app()", "-b", "0.0.0.0:8000"]
