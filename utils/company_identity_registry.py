"""Persistent company identity registry — shared across news, underground, SEC, Telegram."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from utils.company_resolver import is_placeholder

_PLACEHOLDER_NAMES = frozenset({
    "unknown", "n/a", "none", "null", "equities", "market headline",
})


def _clean_symbol(symbol: Any) -> str:
    if not symbol:
        return ""
    return str(symbol).upper().strip()


def _is_real_name(name: Any) -> bool:
    if is_placeholder(name):
        return False
    text = str(name).strip()
    if not text:
        return False
    low = text.lower()
    if low in _PLACEHOLDER_NAMES:
        return False
    if text.startswith("$") and " - " in text:
        return False  # derived "$SYM - headline"
    if text.upper() == text and len(text) <= 5 and text.isalpha():
        return False  # bare ticker as name
    return True


class CompanyIdentityRegistry:
    """Process-wide + disk-backed symbol identity store."""

    _instance: Optional["CompanyIdentityRegistry"] = None
    _lock = threading.Lock()

    def __init__(self, path: Optional[str] = None):
        if path is None:
            try:
                from core.runtime_paths import runtime_path
                path = runtime_path("company_identity.json")
            except Exception:
                root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                path = os.path.join(root, "data", "runtime", "company_identity.json")
        self._path = path
        self._data: Dict[str, Dict[str, Any]] = {}
        self._dirty = False
        self._last_save = 0.0
        self._load()
        self._seed_from_csv()

    @classmethod
    def instance(cls) -> "CompanyIdentityRegistry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _load(self) -> None:
        try:
            if os.path.isfile(self._path):
                with open(self._path, encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    entries = raw.get("entries") if "entries" in raw else raw
                    if isinstance(entries, dict):
                        self._data = {str(k).upper(): v for k, v in entries.items() if isinstance(v, dict)}
        except Exception:
            self._data = {}

    def _seed_from_csv(self) -> None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(root, "data", "company_reference.csv")
        if not os.path.isfile(csv_path):
            return
        try:
            import csv
            with open(csv_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    sym = _clean_symbol(row.get("ticker"))
                    name = (row.get("company_name") or "").strip()
                    if sym and _is_real_name(name) and sym not in self._data:
                        self._data[sym] = {
                            "symbol": sym,
                            "company_name": name,
                            "aliases": [name],
                            "cik": "",
                            "sector": (row.get("sector") or "").strip(),
                            "sources": ["company_reference.csv"],
                            "resolver_status": "cache_exact",
                            "last_price": None,
                            "avg_volume": None,
                            "is_tradeable": True,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "unresolved_entities": [],
                        }
                        self._dirty = True
        except Exception:
            pass

    def save(self, force: bool = False) -> None:
        now = time.time()
        if not force and (not self._dirty or now - self._last_save < 30.0):
            return
        try:
            os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
            payload = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "count": len(self._data),
                "entries": self._data,
            }
            tmp = self._path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            os.replace(tmp, self._path)
            self._dirty = False
            self._last_save = now
        except Exception:
            pass

    def get(self, symbol: Any) -> Optional[Dict[str, Any]]:
        sym = _clean_symbol(symbol)
        if not sym:
            return None
        return self._data.get(sym)

    def company_name(self, symbol: Any) -> Optional[str]:
        row = self.get(symbol)
        if not row:
            return None
        name = row.get("company_name")
        return str(name) if _is_real_name(name) else None

    def remember(
        self,
        symbol: Any,
        *,
        company_name: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        cik: Optional[str] = None,
        sector: Optional[str] = None,
        source: str = "unknown",
        resolver_status: str = "cache_exact",
        last_price: Optional[float] = None,
        avg_volume: Optional[float] = None,
        is_tradeable: bool = True,
        unresolved_entity: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upsert identity. Trusted real names win over derived/blank."""
        sym = _clean_symbol(symbol)
        if not sym:
            return {}
        row = dict(self._data.get(sym) or {
            "symbol": sym,
            "company_name": "",
            "aliases": [],
            "cik": "",
            "sector": "",
            "sources": [],
            "resolver_status": "unknown",
            "last_price": None,
            "avg_volume": None,
            "is_tradeable": True,
            "updated_at": "",
            "unresolved_entities": [],
        })
        if _is_real_name(company_name):
            name = str(company_name).strip()
            if not _is_real_name(row.get("company_name")):
                row["company_name"] = name
            elif name and name not in (row.get("aliases") or []):
                aliases_list = list(row.get("aliases") or [])
                if name not in aliases_list and name != row.get("company_name"):
                    aliases_list.append(name)
                    row["aliases"] = aliases_list[:20]
            row["resolver_status"] = resolver_status or row.get("resolver_status") or "cache_exact"
        if aliases:
            existing = list(row.get("aliases") or [])
            for a in aliases:
                if _is_real_name(a) and a not in existing and a != row.get("company_name"):
                    existing.append(str(a).strip())
            row["aliases"] = existing[:20]
        if cik:
            row["cik"] = str(cik)
        if sector and not is_placeholder(sector):
            row["sector"] = str(sector).strip()
        sources = list(row.get("sources") or [])
        if source and source not in sources:
            sources.append(source)
            row["sources"] = sources[-15:]
        if last_price is not None:
            try:
                p = float(last_price)
                if p > 0:
                    row["last_price"] = p
            except (TypeError, ValueError):
                pass
        if avg_volume is not None:
            try:
                v = float(avg_volume)
                if v > 0:
                    row["avg_volume"] = v
            except (TypeError, ValueError):
                pass
        row["is_tradeable"] = bool(is_tradeable)
        if unresolved_entity and unresolved_entity not in (row.get("unresolved_entities") or []):
            ents = list(row.get("unresolved_entities") or [])
            ents.append(str(unresolved_entity)[:80])
            row["unresolved_entities"] = ents[-10:]
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._data[sym] = row
        self._dirty = True
        if len(self._data) % 25 == 0:
            self.save()
        return row

    def stamp_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Fill blank company_name / price on a news or signal dict from registry."""
        if not isinstance(item, dict):
            return item
        sym = _clean_symbol(item.get("symbol") or item.get("ticker"))
        if not sym:
            return item
        row = self.get(sym)
        if not row:
            return item
        if is_placeholder(item.get("company_name")) and _is_real_name(row.get("company_name")):
            item["company_name"] = row["company_name"]
            item["resolver_status"] = row.get("resolver_status") or "registry"
        price = item.get("price") if item.get("price") is not None else item.get("current_price")
        try:
            has_price = price is not None and float(price) > 0
        except (TypeError, ValueError):
            has_price = False
        if not has_price and row.get("last_price"):
            item["price"] = row["last_price"]
            item["current_price"] = row["last_price"]
        if is_placeholder(item.get("sector")) and row.get("sector"):
            item["sector"] = row["sector"]
        fc = item.get("fact_check")
        if not isinstance(fc, dict):
            fc = {}
            item["fact_check"] = fc
        info = fc.get("company_info")
        if not isinstance(info, dict):
            info = {}
            fc["company_info"] = info
        if _is_real_name(row.get("company_name")):
            info.setdefault("name", row["company_name"])
            info.setdefault("full_name", row["company_name"])
            info.setdefault("company_name", row["company_name"])
            if row.get("sector"):
                info.setdefault("sector", row["sector"])
            if row.get("avg_volume"):
                info.setdefault("avg_volume", row["avg_volume"])
            if fc.get("is_valid") is not True and row.get("resolver_status") in (
                "cache_exact", "sec_exact", "quote_exact", "registry",
            ):
                fc["is_valid"] = True
        return item

    def resolve_for_alert(self, signal: Dict[str, Any]) -> Optional[str]:
        """Return real company name for Telegram, or None if unresolved."""
        sym = _clean_symbol(signal.get("symbol") or signal.get("ticker"))
        fc = signal.get("fact_check") or {}
        info = fc.get("company_info") or {}
        for candidate in (
            signal.get("company_name"),
            info.get("name"),
            info.get("full_name"),
            info.get("company_name"),
            self.company_name(sym) if sym else None,
        ):
            if _is_real_name(candidate):
                return str(candidate).strip()
        return None


def get_identity_registry() -> CompanyIdentityRegistry:
    return CompanyIdentityRegistry.instance()
