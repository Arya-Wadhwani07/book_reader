import json
import os
import subprocess
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
PROJECT = os.environ.get("GCP_PROJECT_ID", "clean-mountain-511522-d0")
REGION = os.environ.get("GCP_REGION", "us-west1")
BUCKET = f"{PROJECT}-book-companion"
RUNTIME = f"book-companion-runtime@{PROJECT}.iam.gserviceaccount.com"
ENV = os.environ | {
    "CLOUDSDK_CONFIG": str(ROOT / ".cache/gcloud"),
    "CLOUDSDK_PYTHON": str(ROOT / ".venv/bin/python"),
    "TMPDIR": str(ROOT / ".cache/tmp"),
    "PYTHONDONTWRITEBYTECODE": "1",
}
GCLOUD = str(ROOT / ".cache/tools/google-cloud-sdk/bin/gcloud")


def gcloud(*args, content=None):
    result = subprocess.run(
        [GCLOUD, *args, "--project", PROJECT, "--quiet"],
        input=content,
        text=True,
        capture_output=True,
        env=ENV,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def provision():
    gcloud(
        "services",
        "enable",
        "run.googleapis.com",
        "cloudbuild.googleapis.com",
        "artifactregistry.googleapis.com",
        "firestore.googleapis.com",
        "storage.googleapis.com",
        "secretmanager.googleapis.com",
        "iam.googleapis.com",
        "iamcredentials.googleapis.com",
        "sts.googleapis.com",
    )
    print("Required APIs enabled.", flush=True)
    accounts = json.loads(gcloud("iam", "service-accounts", "list", "--format=json"))
    if not any(account["email"] == RUNTIME for account in accounts):
        gcloud(
            "iam",
            "service-accounts",
            "create",
            "book-companion-runtime",
            "--display-name=Book Companion runtime",
        )
    gcloud(
        "projects",
        "add-iam-policy-binding",
        PROJECT,
        f"--member=serviceAccount:{RUNTIME}",
        "--role=roles/datastore.user",
        "--condition=None",
    )
    buckets = json.loads(gcloud("storage", "buckets", "list", "--format=json"))
    if not any(
        bucket.get("name") == BUCKET or bucket.get("name") == f"gs://{BUCKET}" for bucket in buckets
    ):
        gcloud(
            "storage",
            "buckets",
            "create",
            f"gs://{BUCKET}",
            f"--location={REGION}",
            "--uniform-bucket-level-access",
        )
    gcloud(
        "storage",
        "buckets",
        "add-iam-policy-binding",
        f"gs://{BUCKET}",
        f"--member=serviceAccount:{RUNTIME}",
        "--role=roles/storage.objectAdmin",
    )
    databases = json.loads(gcloud("firestore", "databases", "list", "--format=json"))
    if not any(database["name"].endswith("/(default)") for database in databases):
        gcloud(
            "firestore",
            "databases",
            "create",
            "--database=(default)",
            f"--location={REGION}",
            "--type=firestore-native",
        )
    repositories = json.loads(
        gcloud("artifacts", "repositories", "list", f"--location={REGION}", "--format=json")
    )
    if not any(repo["name"].endswith("/book-companion") for repo in repositories):
        gcloud(
            "artifacts",
            "repositories",
            "create",
            "book-companion",
            "--repository-format=docker",
            f"--location={REGION}",
        )
    values = dotenv_values(ROOT / ".env")
    secrets = json.loads(gcloud("secrets", "list", "--format=json"))
    existing = {secret["name"].split("/")[-1] for secret in secrets}
    mappings = []
    for key in (
        "SESSION_SECRET",
        "OPENAI_API_KEY",
        "NVIDIA_API_KEY",
        "ANTHROPIC_API_KEY",
        "TAVILY_API_KEY",
        "PINECONE_API_KEY",
    ):
        if not values.get(key):
            continue
        name = "book-companion-" + key.lower().replace("_", "-")
        if name not in existing:
            gcloud("secrets", "create", name, "--replication-policy=automatic")
        gcloud("secrets", "versions", "add", name, "--data-file=-", content=values[key])
        gcloud(
            "secrets",
            "add-iam-policy-binding",
            name,
            f"--member=serviceAccount:{RUNTIME}",
            "--role=roles/secretmanager.secretAccessor",
        )
        mappings.append(f"{key}={name}:latest")
    configuration = {
        "APP_ENV": "cloud",
        "STATE_BACKEND": "firestore",
        "GCP_PROJECT_ID": PROJECT,
        "GCP_REGION": REGION,
        "GCS_BUCKET": BUCKET,
        "INGESTION_JOB": "book-companion-ingest",
        "OPENAI_MODEL": values["OPENAI_MODEL"],
        "NVIDIA_MODEL": values["NVIDIA_MODEL"],
        "ANTHROPIC_MODEL": values["ANTHROPIC_MODEL"],
        "PINECONE_INDEX": values["PINECONE_INDEX"],
        "OPENAI_BUDGET_USD": "5",
        "GENERATION_BUDGET_USD": "2.5",
    }
    output = {
        "project": PROJECT,
        "region": REGION,
        "bucket": BUCKET,
        "runtime": RUNTIME,
        "secrets": ",".join(mappings),
        "environment": ",".join(f"{k}={v}" for k, v in configuration.items()),
    }
    (ROOT / ".cache/cloud_configuration.json").write_text(json.dumps(output, indent=2))
    print("Assignment 2 resources and secret mappings configured.", flush=True)


if __name__ == "__main__":
    provision()
