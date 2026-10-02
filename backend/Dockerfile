FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        libgdal32 \
        libgeos-c1v5 \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY --chown=app:app backend/ /app/
RUN mkdir -p /app/staticfiles \
    && chown app:app /app/staticfiles

USER app

RUN DJANGO_DEBUG=true \
    DJANGO_SECRET_KEY=collectstatic-build-only \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -"]
