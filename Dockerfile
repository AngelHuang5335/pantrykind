FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 BIND_HOST=0.0.0.0 DATABASE_PATH=/data/pantry.sqlite3 DEBUG=false
WORKDIR /app
ARG WITH_POSTGRES=false
COPY requirements.txt requirements-postgres.txt ./
RUN if [ "$WITH_POSTGRES" = "true" ]; then pip install --no-cache-dir -r requirements-postgres.txt; else pip install --no-cache-dir -r requirements.txt; fi \
    && useradd --create-home --uid 10001 pantry && mkdir /data && chown pantry:pantry /data
COPY --chown=pantry:pantry . .
USER pantry
RUN DEBUG=true python manage.py collectstatic --noinput
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=3)"
CMD ["sh", "-c", "python manage.py migrate --noinput && python serve.py"]
