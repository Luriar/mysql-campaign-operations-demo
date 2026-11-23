import tempfile
import unittest
from pathlib import Path
from operations import Operations


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.ops=Operations(Path(self.tmp.name)/"main.sqlite")

    def tearDown(self):
        self.ops.close()
        self.tmp.cleanup()

    def test_duplicate_and_replied_exclusion(self):
        self.ops.import_contacts([{"code":"a"},{"code":"b"},{"code":"a"}])
        self.assertEqual(self.ops.metrics()["contacts"],2)
        self.assertEqual(self.ops.pending(),["a","b"])
        self.ops.mark_replied(["a"])
        self.assertEqual(self.ops.pending(),["b"])

    def test_bad_batch_rolls_back(self):
        with self.assertRaises(ValueError):
            self.ops.import_contacts([{"code":"valid"},{"code":"","eligible":True}])
        self.assertEqual(self.ops.metrics()["contacts"],0)

    def test_reingest_preserves_reply_status(self):
        self.ops.import_contacts([{"code":"x"}])
        self.ops.mark_replied(["x"])
        self.ops.import_contacts([{"code":"x","eligible":True}])
        self.assertEqual(self.ops.pending(),[])

    def test_backup_reopens(self):
        self.ops.import_contacts([{"code":"a"}])
        backup=Path(self.tmp.name)/"copy.sqlite"
        self.ops.backup(backup)
        other=Operations(backup)
        try:
            self.assertEqual(other.pending(),["a"])
        finally:
            other.close()

    def test_template_validation(self):
        with self.assertRaises(ValueError):
            self.ops.change_template("","empty")
        self.ops.change_template("intro","hello")
        self.assertEqual(self.ops.metrics()["audit_events"],1)


if __name__=="__main__":
    unittest.main()
