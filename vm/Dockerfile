# DownTube 서버 컨테이너 — 어느 클라우드 VM(x86/ARM)에서든 동일하게 실행
FROM python:3.12-slim

# ffmpeg(변환) + curl(cloudflared 내려받기) + aria2(초고속 다운로더)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl ca-certificates aria2 \
    && rm -rf /var/lib/apt/lists/*

# cloudflared 설치 (빌드 아키텍처에 맞는 바이너리)
ARG TARGETARCH
RUN curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${TARGETARCH}" \
      -o /usr/local/bin/cloudflared \
    && chmod +x /usr/local/bin/cloudflared

WORKDIR /app
COPY vm/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY static/ ./static/
COPY vm/update_kv.py vm/entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
