"""Safe-write protection guard for SPI NOR flash wear mitigation."""
import datetime
import hashlib
import json
import os
from typing import Any, Dict, Optional, Tuple


class GuardStateError(Exception):
    """The ledger exists but cannot be read; writes are refused until a person fixes it."""


class SafeWriteGuard:
    """Guard tracking flash write budget per device address."""

    def __init__(
        self,
        state_dir: Optional[str] = None,
        min_interval_seconds: float = 0.5,
        daily_write_cap: int = 50,
    ) -> None:
        if state_dir is None:
            state_dir = os.path.expanduser("~/.rewatch/safe_write")
        self.state_dir = state_dir
        self.min_interval = min_interval_seconds
        self.daily_cap = daily_write_cap

    def _state_file(self, address: str) -> str:
        addr_hash = hashlib.sha256(address.upper().encode("utf-8")).hexdigest()[:16]
        return os.path.join(self.state_dir, f"state_{addr_hash}.json")

    @staticmethod
    def _fresh_state() -> Dict[str, Any]:
        return {
            "date": datetime.date.today().isoformat(),
            "daily_count": 0,
            "last_write_timestamp": 0.0,
            "last_payload_sha256": "",
            "total_writes": 0,
        }

    def _load_state(self, address: str) -> Dict[str, Any]:
        """Load the ledger. A missing file is a fresh device; an unreadable one raises
        GuardStateError so the budget is never silently reset (fail closed)."""
        path = self._state_file(address)
        if not os.path.isfile(path):
            return self._fresh_state()
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
            if not isinstance(state, dict) or not isinstance(state.get("daily_count"), int):
                raise ValueError("unexpected ledger contents")
        except (OSError, ValueError) as exc:
            raise GuardStateError(f"safe-write ledger {path} is unreadable ({exc}); inspect or remove it by hand") from exc
        today = datetime.date.today().isoformat()
        if state.get("date") != today:
            state["date"] = today
            state["daily_count"] = 0
        return state

    def _save_state(self, address: str, state: Dict[str, Any]) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        path = self._state_file(address)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, path)  # atomic: a crash never leaves a half-written ledger

    def check_allowed(
        self,
        address: str,
        payload: bytes,
        allow_identical: bool = False,
        dry_run: bool = False,
    ) -> Tuple[bool, str]:
        """Check if a write operation is permitted under safety rules."""
        if dry_run:
            return True, "Dry-run mode: write permitted without state mutation"

        try:
            state = self._load_state(address)
        except GuardStateError as exc:
            return False, str(exc)
        now = datetime.datetime.now().timestamp()
        payload_hash = hashlib.sha256(payload).hexdigest()

        if state["daily_count"] >= self.daily_cap:
            return False, f"Daily flash write cap ({self.daily_cap}) reached for device {address[:8]}..."

        if not allow_identical and state.get("last_payload_sha256") == payload_hash:
            return False, "Delta skip: identical payload has already been written to device"

        elapsed = now - state.get("last_write_timestamp", 0.0)
        if elapsed < self.min_interval:
            return False, f"Rate limit: minimum write interval {self.min_interval}s not met (elapsed: {elapsed:.2f}s)"

        return True, "Write permitted by safe-write guard"

    def record_success(self, address: str, payload: bytes, dry_run: bool = False) -> None:
        """Record a successful device write in the guard ledger."""
        if dry_run:
            return

        state = self._load_state(address)
        now = datetime.datetime.now().timestamp()
        payload_hash = hashlib.sha256(payload).hexdigest()

        state["daily_count"] = state.get("daily_count", 0) + 1
        state["total_writes"] = state.get("total_writes", 0) + 1
        state["last_write_timestamp"] = now
        state["last_payload_sha256"] = payload_hash

        self._save_state(address, state)
