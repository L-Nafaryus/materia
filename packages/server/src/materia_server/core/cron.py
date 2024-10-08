from typing import Optional, Self
from celery import Celery
from pydantic import RedisDsn
from threading import Thread
from materia_server.core.logging import Logger


class CronError(Exception):
    pass


class Cron:
    __instance__: Optional[Self] = None

    def __init__(
        self,
        workers_count: int,
        backend: Celery,
    ):
        self.workers_count = workers_count
        self.backend = backend
        self.workers = []
        self.worker_threads = []

        Cron.__instance__ = self

    @staticmethod
    def new(
        workers_count: int = 1,
        backend_url: Optional[RedisDsn] = None,
        broker_url: Optional[RedisDsn] = None,
        test_connection: bool = True,
        **kwargs,
    ):
        cron = Cron(
            workers_count,
            # TODO: change log level
            # TODO: exclude pickle
            # TODO: disable startup banner
            Celery(
                "cron",
                backend=backend_url,
                broker=broker_url,
                broker_connection_retry_on_startup=True,
                task_serializer="pickle",
                accept_content=["pickle", "json"],
                **kwargs,
            ),
        )

        for _ in range(workers_count):
            cron.workers.append(cron.backend.Worker())

        if test_connection:
            try:
                if logger := Logger.instance():
                    logger.debug("Testing cron broker connection")
                cron.backend.broker_connection().ensure_connection(max_retries=3)
            except Exception as e:
                raise CronError(f"Failed to connect cron broker: {broker_url}") from e

        return cron

    @staticmethod
    def instance() -> Optional[Self]:
        return Cron.__instance__

    def run_workers(self):
        for worker in self.workers:
            thread = Thread(target=worker.start, daemon=True)
            self.worker_threads.append(thread)
            thread.start()
