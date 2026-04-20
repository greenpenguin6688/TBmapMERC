"""
state_manager.py
================
Persistent scan-state with per-position cooldown tracking.

Two JSON files are maintained:
  scan_state.json  – tracks every (kingdom, col, row) position that has been
                     visited, along with a Unix timestamp.  Used for cooldown
                     gating so the same tile is not re-scanned within N seconds.
  finds_log.json   – append-only log of every confirmed Exchange match.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


class StateManager:
    def __init__(self, scan_log_path: str, find_log_path: str, cooldown: int):
        self._scan_path = Path(scan_log_path)
        self._find_path = Path(find_log_path)
        self.cooldown   = cooldown

        # In-memory scan state: { position_key: timestamp }
        self._scanned: dict[str, float] = self._load_scan_log()

    # ── persistence ──────────────────────────────────────────────────────────

    def _load_scan_log(self) -> dict[str, float]:
        if self._scan_path.exists():
            try:
                data = json.loads(self._scan_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save_scan_log(self) -> None:
        self._scan_path.write_text(
            json.dumps(self._scanned, indent=2), encoding="utf-8"
        )

    def _append_find(self, entry: dict) -> None:
        finds: list = []
        if self._find_path.exists():
            try:
                finds = json.loads(self._find_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                finds = []
        finds.append(entry)
        self._find_path.write_text(
            json.dumps(finds, indent=2), encoding="utf-8"
        )

    # ── key helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _key(kingdom_id: int, col: int, row: int) -> str:
        return f"K{kingdom_id}_{col}_{row}"

    # ── public API ───────────────────────────────────────────────────────────

    def is_on_cooldown(self, kingdom_id: int, col: int, row: int) -> bool:
        """Return True if this position was scanned recently (within cooldown)."""
        key = self._key(kingdom_id, col, row)
        ts  = self._scanned.get(key)
        if ts is None:
            return False
        return (time.time() - ts) < self.cooldown

    def mark_scanned(self, kingdom_id: int, col: int, row: int) -> None:
        """Record that this position has just been scanned."""
        key = self._key(kingdom_id, col, row)
        self._scanned[key] = time.time()
        self._save_scan_log()

    def log_find(
        self,
        kingdom_id: int,
        map_coords: str,
        screen_xy: tuple[int, int],
    ) -> dict:
        """Append a confirmed Exchange find to finds_log.json and return the entry."""
        entry = {
            "timestamp":  time.time(),
            "kingdom":    kingdom_id,
            "map_coords": map_coords,
            "screen_xy":  list(screen_xy),
        }
        self._append_find(entry)
        return entry

    def purge_expired(self) -> int:
        """Remove entries older than the cooldown window. Returns the count removed."""
        cutoff  = time.time() - self.cooldown
        expired = [k for k, ts in self._scanned.items() if ts < cutoff]
        for k in expired:
            del self._scanned[k]
        if expired:
            self._save_scan_log()
        return len(expired)
