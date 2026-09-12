"""
Unit Tests untuk Task Scheduler & Background Timer (Sprint 7).
Menguji penundaan tugas, eksekusi callback, pembatalan task, isolasi failsafe,
serta tool deklaratif registry.
"""

import time
import unittest
from unittest.mock import MagicMock

from agent.safety import abort, is_aborted, reset_panic
from agent.scheduler import TaskScheduler
from agent.tools.registry import cancel_scheduled_task, list_active_tasks, schedule_task


class TestTaskScheduler(unittest.TestCase):
    """Pengujian terpadu TaskScheduler dan tools penjadwalan."""

    def setUp(self):
        reset_panic()
        self.scheduler = TaskScheduler()

    def tearDown(self):
        self.scheduler.shutdown(wait=False)
        reset_panic()

    def test_schedule_delay_executes_callback(self):
        """Memastikan tugas one-shot dieksekusi setelah durasi penundaan."""
        executed = []

        def sample_action():
            executed.append("DONE")

        task_id = self.scheduler.schedule_delay(
            delay_seconds=1,
            callback=sample_action,
            task_name="Tes Delay Singkat",
        )

        self.assertIsNotNone(task_id)
        # Tunggu 1.3 detik untuk eksekusi
        time.sleep(1.3)
        self.assertEqual(executed, ["DONE"])

    def test_cancel_scheduled_task(self):
        """Memastikan tugas terjadwal dapat dibatalkan sebelum dieksekusi."""
        executed = []

        def sample_action():
            executed.append("SHOULD_NOT_RUN")

        task_id = self.scheduler.schedule_delay(
            delay_seconds=2,
            callback=sample_action,
            task_name="Tugas yang Akan Dibatalkan",
        )

        ok = self.scheduler.cancel_task(task_id)
        self.assertTrue(ok)

        # Tunggu dan pastikan callback tidak pernah terpanggil
        time.sleep(2.2)
        self.assertEqual(executed, [])

    def test_active_tasks_listing(self):
        """Memastikan get_active_tasks mengembalikan daftar tugas yang valid."""
        task_id = self.scheduler.schedule_delay(
            delay_seconds=5,
            callback=lambda: None,
            task_name="Tugas Aktif 1",
        )

        active = self.scheduler.get_active_tasks()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["task_id"], task_id)
        self.assertEqual(active[0]["task_name"], "Tugas Aktif 1")

        self.scheduler.cancel_task(task_id)
        self.assertEqual(len(self.scheduler.get_active_tasks()), 0)

    def test_scheduled_task_blocked_when_aborted(self):
        """Memastikan eksekusi tugas otomatis dibatalkan jika sistem dalam status darurat (Aborted)."""
        executed = []

        def sample_action():
            executed.append("TRIGGERED")

        self.scheduler.schedule_delay(
            delay_seconds=1,
            callback=sample_action,
            task_name="Tugas Saat Panic",
        )

        # Picu darurat sebelum delay selesai
        abort()
        self.assertTrue(is_aborted())

        time.sleep(1.3)
        # Callback harus dicegah
        self.assertEqual(executed, [])

    def test_declarative_tools_integration(self):
        """Memastikan declarative tools registry untuk scheduling berjalan dengan baik."""
        res_sched = schedule_task(
            task_name="Minum Air",
            delay_seconds=10,
            message_or_action="Ingat minum air putih, Sayang",
        )
        self.assertEqual(res_sched.get("status"), "success")
        task_id = res_sched.get("task_id")
        self.assertIsNotNone(task_id)

        res_list = list_active_tasks()
        self.assertEqual(res_list.get("status"), "success")
        self.assertGreaterEqual(res_list.get("total_tasks"), 1)

        res_cancel = cancel_scheduled_task(task_id)
        self.assertEqual(res_cancel.get("status"), "success")

    def test_tools_blocked_on_emergency(self):
        """Memastikan tools scheduling menolak aksi jika tombol darurat aktif."""
        abort()
        res = schedule_task("Tugas Terlarang", 5, "Aksi")
        self.assertEqual(res.get("status"), "aborted")


if __name__ == "__main__":
    unittest.main()
