import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from demo import open_database,upsert_targets,mark_replied,pending_targets,safe_snapshot

class OperationsTests(unittest.TestCase):
    def test_dedup_and_exclusion(self):
        db=open_database();upsert_targets(db,["a","b","a"])
        mark_replied(db,["b"])
        self.assertEqual(pending_targets(db),["a"])
        self.assertIn("CREATE TABLE",safe_snapshot(db))
        db.close()

if __name__ == "__main__":
    unittest.main()
