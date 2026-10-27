import json
import os
import subprocess

from scripts.cloud_setup import PROJECT, ROOT, RUNTIME, gcloud

REPOSITORY = "Arya-Wadhwani07/book_reader"
DEPLOYER = f"book-companion-deploy@{PROJECT}.iam.gserviceaccount.com"


def github(*arguments):
    executable = next((ROOT / ".cache/tools").glob("gh_*/bin/gh"))
    env = os.environ | {"GH_CONFIG_DIR": str(ROOT / ".cache/github")}
    result = subprocess.run(
        [str(executable), *arguments], env=env, capture_output=True, text=True, check=True
    )
    return result.stdout


def configure():
    project = json.loads(gcloud("projects", "describe", PROJECT, "--format=json"))
    number = project["projectNumber"]
    accounts = json.loads(gcloud("iam", "service-accounts", "list", "--format=json"))
    if not any(account["email"] == DEPLOYER for account in accounts):
        gcloud("iam", "service-accounts", "create", "book-companion-deploy")
    for role in ("roles/run.admin", "roles/artifactregistry.writer"):
        gcloud(
            "projects",
            "add-iam-policy-binding",
            PROJECT,
            f"--member=serviceAccount:{DEPLOYER}",
            f"--role={role}",
            "--condition=None",
        )
    gcloud(
        "iam",
        "service-accounts",
        "add-iam-policy-binding",
        RUNTIME,
        f"--member=serviceAccount:{DEPLOYER}",
        "--role=roles/iam.serviceAccountUser",
    )
    pools = json.loads(
        gcloud("iam", "workload-identity-pools", "list", "--location=global", "--format=json")
    )
    if not any(pool["name"].endswith("/book-companion-github") for pool in pools):
        gcloud(
            "iam",
            "workload-identity-pools",
            "create",
            "book-companion-github",
            "--location=global",
            "--display-name=Book Companion GitHub",
        )
    providers = json.loads(
        gcloud(
            "iam",
            "workload-identity-pools",
            "providers",
            "list",
            "--workload-identity-pool=book-companion-github",
            "--location=global",
            "--format=json",
        )
    )
    if not any(provider["name"].endswith("/github") for provider in providers):
        gcloud(
            "iam",
            "workload-identity-pools",
            "providers",
            "create-oidc",
            "github",
            "--workload-identity-pool=book-companion-github",
            "--location=global",
            "--issuer-uri=https://token.actions.githubusercontent.com",
            "--attribute-mapping=google.subject=assertion.sub,attribute.repository=assertion.repository",
            f"--attribute-condition=assertion.repository == '{REPOSITORY}' && assertion.ref == 'refs/heads/main'",
        )
    gcloud(
        "iam",
        "service-accounts",
        "add-iam-policy-binding",
        DEPLOYER,
        f"--member=principalSet://iam.googleapis.com/projects/{number}/locations/global/workloadIdentityPools/book-companion-github/attribute.repository/{REPOSITORY}",
        "--role=roles/iam.workloadIdentityUser",
    )
    config = json.loads((ROOT / ".cache/cloud_configuration.json").read_text())
    variables = {
        "GCP_WORKLOAD_IDENTITY_PROVIDER": f"projects/{number}/locations/global/workloadIdentityPools/book-companion-github/providers/github",
        "GCP_DEPLOY_SERVICE_ACCOUNT": DEPLOYER,
        "GCP_RUNTIME_SERVICE_ACCOUNT": RUNTIME,
        "CLOUD_RUN_SECRETS": config["secrets"],
        "CLOUD_RUN_ENV_VARS": config["environment"],
        "SMOKE_QUERY": "Use semantic retrieval to explain one central event or idea from this book and cite original passages.",
    }
    for name, value in variables.items():
        github("variable", "set", name, "--repo", REPOSITORY, "--body", value)
    print(
        "Repository-scoped, main-branch Workload Identity Federation and deployment variables configured.",
        flush=True,
    )


if __name__ == "__main__":
    configure()
