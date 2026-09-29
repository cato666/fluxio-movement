FROM python:3.11.14-slim-bookworm@sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgles2 \
    libegl1 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt constraints.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p models && \
    curl --fail --location --retry 3 \
    -o models/pose_landmarker_lite.task \
    https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task \
    && echo "59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a  models/pose_landmarker_lite.task" | sha256sum --check

EXPOSE 8000

RUN chmod +x scripts/start-app.sh

CMD ["./scripts/start-app.sh"]

FROM runtime AS test
RUN pip install --no-cache-dir -r requirements-test.txt
CMD ["pytest", "-q"]

FROM runtime AS production
