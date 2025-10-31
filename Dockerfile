# Multi-service image: select target via ARG SERVICE (gov|commercial)
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY gov_service.py commercial_service.py perf_test.py /app/

ARG SERVICE=gov
ENV SERVICE=${SERVICE}

# Default ports
EXPOSE 8080 8081

CMD ["sh", "-c", "if [ \"$SERVICE\" = \"gov\" ]; then python gov_service.py --host 0.0.0.0 --port 8080; else python commercial_service.py --host 0.0.0.0 --port 8081; fi"]



