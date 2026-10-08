from django.conf import settings


def github_repo(request):
    """Expose the public repository URL to the footer (may be empty)."""
    return {'GITHUB_REPO_URL': settings.GITHUB_REPO_URL}
