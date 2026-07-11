FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ORACLE_CLIENT_LIB_DIR=/opt/oracle/instantclient_11_2 \
    LD_LIBRARY_PATH=/opt/oracle/instantclient_11_2

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libaio1 libnsl2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
COPY instantclient_11_2/python-wheels /tmp/python-wheels

RUN pip install --no-cache-dir --no-index --find-links /tmp/python-wheels -r /app/requirements.txt \
    && rm -rf /tmp/python-wheels

COPY instantclient_11_2 /opt/oracle/instantclient_11_2
RUN ln -sf libclntsh.so.11.1 /opt/oracle/instantclient_11_2/libclntsh.so \
    && ln -sf libocci.so.11.1 /opt/oracle/instantclient_11_2/libocci.so

COPY app /app/app

EXPOSE 18080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18080"]
