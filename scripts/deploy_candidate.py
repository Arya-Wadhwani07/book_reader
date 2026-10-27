import json
import os

from scripts.cloud_setup import PROJECT, REGION, ROOT, RUNTIME, gcloud


def deploy():
    configuration = json.loads((ROOT / ".cache/cloud_configuration.json").read_text())
    image = os.environ.get(
        "DEPLOY_IMAGE", f"{REGION}-docker.pkg.dev/{PROJECT}/book-companion/book-companion:initial"
    )
    common = [
        f"--image={image}",
        f"--region={REGION}",
        f"--service-account={RUNTIME}",
        f"--set-secrets={configuration['secrets']}",
        f"--set-env-vars={configuration['environment']}",
    ]
    gcloud(
        "run",
        "jobs",
        "deploy",
        "book-companion-ingest",
        *common,
        "--command=/app/.venv/bin/python",
        "--args=-m,src.rag.ingest",
        "--memory=2Gi",
        "--cpu=1",
        "--tasks=1",
        "--max-retries=0",
        "--task-timeout=3600s",
    )
    gcloud(
        "run",
        "jobs",
        "add-iam-policy-binding",
        "book-companion-ingest",
        f"--region={REGION}",
        f"--member=serviceAccount:{RUNTIME}",
        "--role=roles/run.invoker",
    )
    gcloud(
        "run",
        "deploy",
        "book-companion",
        *common,
        "--allow-unauthenticated",
        "--memory=1Gi",
        "--cpu=1",
        "--concurrency=4",
        "--timeout=300",
        "--min-instances=0",
        "--max-instances=2",
        "--tag=candidate",
    )
    service = json.loads(
        gcloud(
            "run", "services", "describe", "book-companion", f"--region={REGION}", "--format=json"
        )
    )
    result = {
        "url": service["status"]["url"],
        "revision": service["status"]["latestReadyRevisionName"],
        "image": image,
    }
    (ROOT / "reports/deployment.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    deploy()
