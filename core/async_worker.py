from PyQt6.QtCore import QThread, QCoreApplication
import asyncio


class AsyncWorker(QThread):
    """Поток для выполнения asyncio-операций из Qt"""

    def __init__(self):
        super().__init__()
        self.loop = None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        finally:
            # Закрываем все оставшиеся задачи
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            # Даём задачам время отмениться
            if pending:
                self.loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
            self.loop.close()

    def submit(self, coro):
        """Отправить coroutine в цикл событий"""
        if self.loop is None or not self.loop.is_running():
            raise RuntimeError("AsyncWorker не запущен")
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def stop(self):
        """Корректно остановить цикл событий"""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)