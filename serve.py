import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from config.wsgi import application
from waitress import serve

if __name__ == "__main__":
    serve(
        application,
        host=os.environ.get("BIND_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        threads=int(os.environ.get("THREADS", "4")),
        max_request_body_size=2 * 1024 * 1024,
    )
