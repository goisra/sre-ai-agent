from config.settings.base import *  # noqa: F403
from config.settings.base import env

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if SECRET_KEY == "insecure-dev-key-do-not-use-in-production":  # noqa: F405
    raise RuntimeError("SECRET_KEY must be set via environment variable in production.")
