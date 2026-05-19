FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---- deps stage ----
FROM base AS deps

RUN pip install hatchling
COPY pyproject.toml .
RUN python3 -c "\
import tomllib, subprocess; \
data = tomllib.load(open('pyproject.toml', 'rb')); \
deps = data['project']['dependencies']; \
subprocess.run(['pip', 'install', '--no-cache-dir'] + deps, check=True)"

# ---- runtime stage ----
FROM base AS runtime

COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY . .

RUN addgroup --system app && adduser --system --group app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
