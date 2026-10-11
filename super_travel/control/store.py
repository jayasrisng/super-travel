"""Local integration store. Production replaces this adapter with Postgres + verified JWTs."""

import hashlib
import json
import os
import sqlite3
import threading
from datetime import UTC, datetime
from uuid import uuid4


class ControlError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


def utcnow():
    return datetime.now(UTC)


class Store:
    def __init__(self, path, now=utcnow):
        self.now = now
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        if str(path) != ":memory:":
            os.chmod(path, 0o600)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("PRAGMA secure_delete=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS objects (
            id TEXT PRIMARY KEY, actor TEXT NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL,
            input TEXT, lease TEXT, lease_until REAL, created REAL NOT NULL, expires REAL
        );
        CREATE INDEX IF NOT EXISTS actor_objects ON objects(actor,kind,created);
        CREATE TABLE IF NOT EXISTS replays (
            actor TEXT, route TEXT, key TEXT, digest TEXT NOT NULL, body TEXT NOT NULL,
            expires REAL NOT NULL, PRIMARY KEY(actor,route,key)
        );
        """)

    def close(self):
        self.db.close()

    def transaction(self, callback):
        with self.lock:
            if self.db.in_transaction:
                return callback()
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.cleanup()
                result = callback()
                self.db.execute("COMMIT")
                return result
            except Exception:
                self.db.execute("ROLLBACK")
                raise

    def cleanup(self):
        now = self.now().timestamp()
        self.db.execute("DELETE FROM replays WHERE expires <= ?", (now,))
        rows = self.db.execute(
            "SELECT id,body FROM objects WHERE kind='run' AND expires<=? AND json_extract(body,'$.status') != 'expired'",
            (now,),
        ).fetchall()
        for row in rows:
            body = json.loads(row["body"])
            body.update(
                status="expired", proposal=None, error=None, version=body["version"] + 1
            )
            self.db.execute(
                "UPDATE objects SET body=?,input=NULL,lease=NULL,lease_until=NULL WHERE id=?",
                (json.dumps(body), row["id"]),
            )
        # Remove tombstones a day after expiry; no location/request content survives expiry.
        self.db.execute(
            "DELETE FROM objects WHERE kind='run' AND expires<=?", (now - 86400,)
        )

    def get(self, actor, kind, identifier):
        row = self.db.execute(
            "SELECT body FROM objects WHERE id=? AND actor=? AND kind=?",
            (str(identifier), str(actor), kind),
        ).fetchone()
        if not row:
            raise ControlError(404, "not_found", "Resource not found")
        return json.loads(row["body"])

    def insert(self, actor, kind, body, request=None):
        self.db.execute(
            "INSERT INTO objects(id,actor,kind,body,input,created,expires) VALUES(?,?,?,?,?,?,?)",
            (
                body["id"],
                str(actor),
                kind,
                json.dumps(body),
                json.dumps(request) if request else None,
                self.now().timestamp(),
                datetime.fromisoformat(body["expires_at"]).timestamp()
                if kind == "run"
                else None,
            ),
        )

    def create(self, actor, route, key, request, factory):
        digest = hashlib.sha256(
            json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        def operation():
            previous = self.db.execute(
                "SELECT digest,body FROM replays WHERE actor=? AND route=? AND key=?",
                (str(actor), route, str(key)),
            ).fetchone()
            if previous:
                if previous["digest"] != digest:
                    raise ControlError(
                        409,
                        "idempotency_conflict",
                        "This key was used with different input",
                    )
                return json.loads(previous["body"])
            body = factory()
            self.db.execute(
                "INSERT INTO replays VALUES(?,?,?,?,?,?)",
                (
                    str(actor),
                    route,
                    str(key),
                    digest,
                    json.dumps(body),
                    self.now().timestamp() + 86400,
                ),
            )
            return body

        return self.transaction(operation)

    def list(self, actor, kind, cursor=None, limit=20, trip_id=None):
        query = "SELECT body FROM objects WHERE actor=? AND kind=?"
        params = [str(actor), kind]
        if trip_id is not None:
            query += " AND json_extract(body,'$.trip_id')=?"
            params.append(str(trip_id))
        rows = self.db.execute(query + " ORDER BY created DESC,id DESC", params).fetchall()
        values = [json.loads(row["body"]) for row in rows]
        if cursor:
            positions = [
                index for index, item in enumerate(values) if item["id"] == str(cursor)
            ]
            if not positions:
                raise ControlError(
                    400, "invalid_cursor", "Cursor does not belong to this collection"
                )
            values = values[positions[0] + 1 :]
        page = values[:limit]
        return page, page[-1]["id"] if len(values) > limit else None

    def claim(self):
        def operation():
            now = self.now().timestamp()
            rows = self.db.execute(
                "SELECT * FROM objects WHERE kind='run' AND input IS NOT NULL ORDER BY created,id"
            ).fetchall()
            for row in rows:
                body = json.loads(row["body"])
                if body["status"] == "queued" or (
                    body["status"] == "running" and (row["lease_until"] or 0) <= now
                ):
                    lease = str(uuid4())
                    body.update(status="running", version=body["version"] + 1)
                    self.db.execute(
                        "UPDATE objects SET body=?,lease=?,lease_until=? WHERE id=?",
                        (json.dumps(body), lease, now + 120, row["id"]),
                    )
                    return body, json.loads(row["input"]), lease
            return None

        return self.transaction(operation)

    def finish(self, identifier, lease, proposal=None, error=None):
        def operation():
            row = self.db.execute(
                "SELECT body,lease FROM objects WHERE id=?", (identifier,)
            ).fetchone()
            if not row or row["lease"] != lease:
                return
            body = json.loads(row["body"])
            if body["status"] != "running":
                return
            body.update(
                status="failed" if error else "succeeded",
                proposal=proposal,
                error=error,
                version=body["version"] + 1,
            )
            self.db.execute(
                "UPDATE objects SET body=?,lease=NULL,lease_until=NULL WHERE id=?",
                (json.dumps(body), identifier),
            )

        self.transaction(operation)

    def cancel(self, actor, identifier, etag):
        def operation():
            body = self.get(actor, "run", identifier)
            if etag is None:
                raise ControlError(428, "precondition_required", "If-Match is required")
            if etag != f'"{body["version"]}"':
                raise ControlError(
                    412, "version_conflict", "Read the latest run before cancelling"
                )
            if body["status"] in ("queued", "running"):
                body.update(status="cancelled", version=body["version"] + 1)
                self.db.execute(
                    "UPDATE objects SET body=?,lease=NULL,lease_until=NULL,input=NULL WHERE id=?",
                    (json.dumps(body), str(identifier)),
                )
            return body

        return self.transaction(operation)
