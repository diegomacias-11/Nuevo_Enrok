import json
import os
import subprocess
from datetime import datetime

from django.core.management.base import BaseCommand
from google.cloud import storage
from google.oauth2 import service_account


class Command(BaseCommand):
    help = "Backup Postgres DB and upload to Google Cloud Storage"

    def handle(self, *args, **kwargs):
        database_url = os.environ.get("DATABASE_URL")
        bucket_name = os.environ.get("GS_BUCKET_NAME")
        credentials_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")

        if not database_url:
            self.stderr.write("Falta DATABASE_URL")
            return

        if not bucket_name:
            self.stderr.write("Falta GS_BUCKET_NAME")
            return

        if not credentials_json:
            self.stderr.write("Falta GOOGLE_APPLICATION_CREDENTIALS_JSON")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"backup_{timestamp}.sql"

        self.stdout.write("Creando backup de la base de datos...")

        try:
            subprocess.run(
                ["pg_dump", database_url, "-f", filename],
                check=True,
            )
        except Exception as e:
            self.stderr.write(f"Error al hacer pg_dump: {e}")
            return

        self.stdout.write("Subiendo backup a Google Cloud Storage...")

        try:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(credentials_json)
            )

            client = storage.Client(
                credentials=credentials,
                project=credentials.project_id,
            )

            bucket = client.bucket(bucket_name)
            blob = bucket.blob(f"backups/{filename}")
            blob.upload_from_filename(filename)

            self.stdout.write(f"Backup subido correctamente: backups/{filename}")

        except Exception as e:
            self.stderr.write(f"Error al subir a GCS: {e}")

        finally:
            if os.path.exists(filename):
                os.remove(filename)
