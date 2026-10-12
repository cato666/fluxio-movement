FROM postgres:17.6-bookworm@sha256:f3bd19c606e442c3d7bdfa8002e03fe260a1023351e0ea4598032022b68dd6e3 AS rootfs
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates tzdata && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/backup-venv
COPY backup-runner/requirements.txt /tmp/backup-requirements.txt
RUN /opt/backup-venv/bin/pip install --no-cache-dir -r /tmp/backup-requirements.txt
RUN useradd --uid 10001 --create-home fluxio-backup && mkdir -p /work /state && chown fluxio-backup:fluxio-backup /work /state
COPY scripts/pilot_backup_runner.py scripts/pilot_backup_restore.py scripts/pilot_backup_bundle.py scripts/pilot_backup_ops.py scripts/pilot_telegram_alerts.py scripts/pilot_resend_alerts.py /opt/fluxio-backup/
COPY app/media_protocol.py /opt/fluxio-backup/media_protocol.py
# Reset inherited Postgres image VOLUME/entrypoint metadata. No anonymous PGDATA.
FROM scratch
COPY --from=rootfs / /
ENV PATH=/usr/lib/postgresql/17/bin:/opt/backup-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/home/fluxio-backup PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 BACKUP_RUNNER_ENABLED=false BACKUP_SCHEDULE_ENABLED=false TELEGRAM_ALERTS_ENABLED=false
USER 10001:10001
ENTRYPOINT ["/opt/backup-venv/bin/python", "/opt/fluxio-backup/pilot_backup_runner.py"]
CMD ["schedule"]
