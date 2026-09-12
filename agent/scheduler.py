"""
Task Scheduler & Background Timer Engine untuk Wellmy-Ai.
Menggunakan APScheduler BackgroundScheduler dengan proteksi failsafe isolasi (Rule 03).
Mendukung one-shot delay timer, recurring tasks, dan pembatalan task.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from agent.safety import is_aborted

logger = logging.getLogger("wellmy.scheduler")

# Singleton instance
_global_scheduler: Optional["TaskScheduler"] = None


class TaskScheduler:
    """
    Penjadwal tugas latar belakang untuk pengingat dan aksi otomatis Wellmy-Ai.
    Terintegrasi dengan sistem penghenti darurat global.
    """

    def __init__(self):
        self._scheduler = BackgroundScheduler(daemon=True)
        self._tasks_metadata: Dict[str, Dict[str, Any]] = {}
        self._is_started = False

    def start(self) -> None:
        """Memulai background scheduler jika belum berjalan."""
        if not self._is_started:
            self._scheduler.start()
            self._is_started = True
            logger.info("TaskScheduler berhasil dimulai di background thread.")

    def shutdown(self, wait: bool = False) -> None:
        """Menghentikan background scheduler secara aman."""
        if self._is_started:
            self._scheduler.shutdown(wait=wait)
            self._is_started = False
            self._tasks_metadata.clear()
            logger.info("TaskScheduler berhasil dinonaktifkan.")

    def _wrap_safe_callback(self, task_id: str, callback: Callable[..., Any], task_name: str) -> Callable[..., Any]:
        """Membungkus callback tugas dengan verifikasi failsafe is_aborted()."""
        def safe_execution(*args, **kwargs):
            if is_aborted():
                logger.warning(f"Tugas terjadwal '{task_name}' ({task_id}) dibatalkan karena sistem dalam keadaan darurat (Aborted).")
                self._tasks_metadata.pop(task_id, None)
                return None

            try:
                logger.info(f"Mengeksekusi tugas terjadwal: '{task_name}' ({task_id})")
                res = callback(*args, **kwargs)
                return res
            except Exception as e:
                logger.error(f"Terjadi kesalahan saat menjalankan tugas terjadwal '{task_name}': {e}")
                return None
            finally:
                # Jika job bukan interval (one-shot), hapus metadata
                job = self._scheduler.get_job(task_id)
                if not job:
                    self._tasks_metadata.pop(task_id, None)

        return safe_execution

    def schedule_delay(
        self,
        delay_seconds: int,
        callback: Callable[..., Any],
        task_name: str = "Tugas Terjadwal",
        args: Optional[List[Any]] = None,
    ) -> str:
        """
        Menjadwalkan eksekusi aksi satu kali setelah penundaan beberapa detik.

        Args:
            delay_seconds: Jumlah detik penundaan.
            callback: Fungsi yang akan dieksekusi.
            task_name: Nama deskriptif tugas.
            args: Argumen posisi untuk fungsi callback.
        """
        self.start()
        task_id = str(uuid.uuid4())[:8]
        run_time = datetime.now() + timedelta(seconds=max(1, delay_seconds))

        safe_cb = self._wrap_safe_callback(task_id, callback, task_name)
        trigger = DateTrigger(run_date=run_time)

        self._scheduler.add_job(
            safe_cb,
            trigger=trigger,
            args=args or [],
            id=task_id,
            name=task_name,
            replace_existing=True,
        )

        self._tasks_metadata[task_id] = {
            "task_id": task_id,
            "task_name": task_name,
            "trigger_type": "delay",
            "run_time": run_time.isoformat(),
            "delay_seconds": delay_seconds,
        }

        logger.info(f"Tugas dijadwalkan: '{task_name}' (ID: {task_id}) dalam {delay_seconds} detik.")
        return task_id

    def schedule_interval(
        self,
        interval_seconds: int,
        callback: Callable[..., Any],
        task_name: str = "Tugas Interval",
        args: Optional[List[Any]] = None,
    ) -> str:
        """
        Menjadwalkan eksekusi tugas berulang secara berkala.
        """
        self.start()
        task_id = str(uuid.uuid4())[:8]
        safe_cb = self._wrap_safe_callback(task_id, callback, task_name)
        trigger = IntervalTrigger(seconds=max(1, interval_seconds))

        self._scheduler.add_job(
            safe_cb,
            trigger=trigger,
            args=args or [],
            id=task_id,
            name=task_name,
            replace_existing=True,
        )

        self._tasks_metadata[task_id] = {
            "task_id": task_id,
            "task_name": task_name,
            "trigger_type": "interval",
            "interval_seconds": interval_seconds,
            "created_at": datetime.now().isoformat(),
        }

        logger.info(f"Tugas berulang dijadwalkan: '{task_name}' (ID: {task_id}) setiap {interval_seconds} detik.")
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """Membatalkan tugas terjadwal berdasarkan ID."""
        try:
            self._scheduler.remove_job(task_id)
            self._tasks_metadata.pop(task_id, None)
            logger.info(f"Tugas terjadwal dibatalkan: ID {task_id}")
            return True
        except Exception:
            logger.warning(f"Gagal membatalkan tugas terjadwal: ID {task_id} tidak ditemukan.")
            return False

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Mengambil daftar seluruh tugas terjadwal yang sedang aktif."""
        active = []
        for task_id, meta in list(self._tasks_metadata.items()):
            job = self._scheduler.get_job(task_id)
            if job:
                active.append(meta)
            else:
                self._tasks_metadata.pop(task_id, None)
        return active


def get_scheduler() -> TaskScheduler:
    """Mengambil shared singleton instance TaskScheduler."""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = TaskScheduler()
    return _global_scheduler
