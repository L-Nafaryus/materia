from gunicorn.app.wsgiapp import WSGIApplication
import multiprocessing


class MateriaProcessManager(WSGIApplication):
    def __init__(self, app: str, options: dict | None = None):
        self.app_uri = app 
        self.options = options or {}
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

def run():
    options = {
        "bind": "0.0.0.0:8000",
        "workers": (multiprocessing.cpu_count() * 2) + 1,
        "worker_class": "materia.app.wsgi.MateriaWorker",
        "raw_env": ["FOO=1"],
        "user": None,
        "group": None
    }
    MateriaProcessManager("materia.app.app:run", options).run()
