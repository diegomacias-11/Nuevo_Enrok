import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from google.cloud import storage
from google.oauth2 import service_account


BACKUP_PATTERN = re.compile(
    r"backups/backup_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.(?:sql|dump)"
)
RETENTION_DAYS = 30


class Command(BaseCommand):
    help = "Upload a compressed Postgres backup to GCS and retain backups for 30 days"

    def handle(self, *args, **kwargs):
        database_url = os.environ.get("DATABASE_URL")
        bucket_name = os.environ.get("GS_BUCKET_NAME")
        credentials_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")

        for name, value in (
            ("DATABASE_URL", database_url),
            ("GS_BUCKET_NAME", bucket_name),
            ("GOOGLE_APPLICATION_CREDENTIALS_JSON", credentials_json),
        ):
            if not value:
                raise CommandError(f"Falta {name}")

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"backup_{timestamp}.dump"
        backup_name = f"backups/{filename}"
        stage = "preparar el respaldo"

        try:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(credentials_json)
            )
            client = storage.Client(
                credentials=credentials,
                project=credentials.project_id,
            )
            bucket = client.bucket(bucket_name)

            # The temporary directory is removed even if pg_dump or upload fails.
            with tempfile.TemporaryDirectory(prefix="postgres_backup_") as temp_dir:
                filepath = Path(temp_dir) / filename
                stage = "generar el respaldo con pg_dump"
                self.stdout.write("Creando respaldo comprimido de la base de datos...")
                subprocess.run(
                    ["pg_dump", database_url, "-Fc", "-Z", "6", "-f", str(filepath)],
                    check=True,
                )
                size = filepath.stat().st_size
                if size == 0:
                    raise CommandError("pg_dump produjo un respaldo vacío")

                stage = "subir el respaldo a GCS"
                self.stdout.write(f"Subiendo respaldo: {size / (1024 * 1024):.2f} MiB")
                blob = bucket.blob(backup_name)
                # Do not overwrite an existing backup if two jobs share a timestamp.
                blob.upload_from_filename(str(filepath), if_generation_match=0)
                self.stdout.write(f"Respaldo subido correctamente: {backup_name}")

            # Cleanup is only attempted after the new backup was uploaded.
            stage = "eliminar respaldos antiguos"
            cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
            deleted = 0
            for old_blob in client.list_blobs(bucket_name, prefix="backups/"):
                if old_blob.name == backup_name or not BACKUP_PATTERN.fullmatch(old_blob.name):
                    continue
                # Use GCS creation time, not the date claimed by the filename.
                if old_blob.time_created is None or old_blob.time_created >= cutoff:
                    continue
                if old_blob.generation is None:
                    continue
                old_blob.delete(if_generation_match=old_blob.generation)
                deleted += 1
                self.stdout.write(f"Respaldo antiguo eliminado: {old_blob.name}")

            self.stdout.write(
                self.style.SUCCESS(
                    f"Respaldo completado. Respaldos mayores de {RETENTION_DAYS} "
                    f"días eliminados: {deleted}."
                )
            )
        except CommandError:
            raise
        except Exception as exc:
            # Do not include the subprocess command: DATABASE_URL contains credentials.
            raise CommandError(
                f"Error al {stage} ({type(exc).__name__}). "
                "El comando terminó con fallo."
            ) from None
