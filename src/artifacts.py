from pathlib import PurePosixPath


class Artifacts:
    def __init__(self, settings):
        self.settings = settings
        self.directory = settings.data_dir / "files"
        self.bucket = None
        if settings.app_env == "cloud":
            from google.cloud import storage

            self.bucket = storage.Client(project=settings.gcp_project_id).bucket(
                settings.gcs_bucket
            )

    def validate(self, key):
        path = PurePosixPath(key)
        if not path.parts or path.is_absolute() or ".." in path.parts or "\\" in key:
            raise ValueError("Invalid artifact path.")
        if not self.bucket and not (self.directory / key).resolve().is_relative_to(
            self.directory.resolve()
        ):
            raise ValueError("Invalid artifact path: outside my storage directory.")

    def put(self, key, content, content_type="application/octet-stream"):
        self.validate(key)
        if self.bucket:
            self.bucket.blob(key).upload_from_string(content, content_type=content_type)
        else:
            path = self.directory / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def get(self, key):
        self.validate(key)
        if self.bucket:
            return self.bucket.blob(key).download_as_bytes()
        return (self.directory / key).read_bytes()

    def delete(self, key):
        self.validate(key)
        if self.bucket:
            self.bucket.blob(key).delete()
        else:
            (self.directory / key).unlink(missing_ok=True)
