"""Clean-room SQLite demonstration, not the historical MySQL source."""
import sqlite3

def open_database():
    db=sqlite3.connect(":memory:")
    db.execute("CREATE TABLE targets(code TEXT PRIMARY KEY, replied INTEGER NOT NULL DEFAULT 0)")
    db.execute("CREATE TABLE messages(code TEXT PRIMARY KEY, body TEXT NOT NULL)")
    db.commit()
    return db

def upsert_targets(db,codes):
    with db:
        db.executemany("INSERT OR IGNORE INTO targets(code) VALUES (?)",
                       ((code,) for code in codes))

def mark_replied(db,codes):
    with db:
        db.executemany("UPDATE targets SET replied=1 WHERE code=?",
                       ((code,) for code in codes))

def pending_targets(db):
    return [r[0] for r in db.execute(
        "SELECT code FROM targets WHERE replied=0 ORDER BY code").fetchall()]

def safe_snapshot(db):
    return "\n".join(db.iterdump())

if __name__ == "__main__":
    db=open_database()
    upsert_targets(db,["fake-A","fake-B","fake-A"])
    mark_replied(db,["fake-A"])
    print(pending_targets(db))
