"""Independent offline database-operations example; no employer tables or credentials."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path


class Operations:
    def __init__(self, path=":memory:"):
        self.db=sqlite3.connect(str(path))
        self.db.row_factory=sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS contacts(
                code TEXT PRIMARY KEY,
                eligible INTEGER NOT NULL DEFAULT 1,
                replied INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS message_templates(
                name TEXT PRIMARY KEY, content TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL, affected INTEGER NOT NULL
            );
        """)
        self.db.commit()

    def import_contacts(self, records: list[dict]) -> int:
        """One bad input rolls back the entire update."""
        with self.db:
            for obj in records:
                code=obj["code"]
                eligible=obj.get("eligible",True)
                if not isinstance(code,str) or not code.strip():
                    raise ValueError("invalid code")
                if not isinstance(eligible,bool):
                    raise ValueError("eligible must be boolean")
                self.db.execute("""
                    INSERT INTO contacts(code,eligible) VALUES (?,?)
                    ON CONFLICT(code) DO UPDATE SET eligible=excluded.eligible
                """, (code.strip(),int(eligible)))
            self.db.execute("INSERT INTO audit(event,affected) VALUES(?,?)",
                            ("import",len(records)))
        return len(records)

    def mark_replied(self, codes: list[str]) -> int:
        with self.db:
            count=0
            for code in set(codes):
                count+=self.db.execute("UPDATE contacts SET replied=1 WHERE code=?",
                                       (code,)).rowcount
            self.db.execute("INSERT INTO audit(event,affected) VALUES(?,?)",
                            ("mark_replied",count))
        return count

    def change_template(self, name: str, content: str) -> None:
        if not name.strip() or not content.strip():
            raise ValueError("template name and content required")
        with self.db:
            self.db.execute("""INSERT INTO message_templates(name,content) VALUES (?,?)
                ON CONFLICT(name) DO UPDATE SET content=excluded.content""",
                (name,content))
            self.db.execute("INSERT INTO audit(event,affected) VALUES('template_change',1)")

    def pending(self) -> list[str]:
        return [r["code"] for r in self.db.execute(
            "SELECT code FROM contacts WHERE eligible=1 AND replied=0 ORDER BY code"
        )]

    def metrics(self) -> dict:
        return {
            "contacts":self.db.execute("SELECT COUNT(*) FROM contacts").fetchone()[0],
            "eligible_pending":len(self.pending()),
            "audit_events":self.db.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
        }

    def backup(self, destination: str | Path) -> None:
        target=Path(destination)
        if str(target)==":memory:":
            raise ValueError("choose a backup file")
        target.parent.mkdir(parents=True,exist_ok=True)
        copy=sqlite3.connect(str(target))
        try:
            self.db.backup(copy)
        finally:
            copy.close()

    def close(self):
        self.db.close()


if __name__=="__main__":
    ops=Operations()
    try:
        ops.import_contacts([
            {"code":"fictional-01"},{"code":"fictional-02"},
            {"code":"fictional-03","eligible":False}
        ])
        ops.mark_replied(["fictional-02"])
        ops.change_template("welcome","Synthetic demo message")
        print(json.dumps({"pending":ops.pending(),"metrics":ops.metrics(),
                          "synthetic_only":True},ensure_ascii=False,indent=2))
    finally:
        ops.close()
