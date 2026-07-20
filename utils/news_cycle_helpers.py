"""Single-pass news cycle helpers — one ingest, targeted deep dives only."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union

ConfigLike = Union[Dict[str, Any], Any]

_DEFAULT_PIPELINE = {
    "single_ingest_per_cycle": True,
    "deep_investigate_enabled": True,
    "deep_investigate_max_items": 12,
    "deep_investigate_min_score": 0.45,
    "max_news_age_days": 7,
    "freshness_classes": {
        "BREAKING": 2,
        "INTRADAY": 18,
        "RECENT_CATALYST": 72,
        "BACKGROUND": 168,
    },
}


def news_pipeline_config(config: ConfigLike) -> Dict[str, Any]:
    if config is None:
        return dict(_DEFAULT_PIPELINE)
    data = config.data if hasattr(config, "data") else config
    if not isinstance(data, dict):
        return dict(_DEFAULT_PIPELINE)
    merged = dict(_DEFAULT_PIPELINE)
    merged.update(data.get("news_pipeline") or {})
    return merged


def news_item_key(item: Dict[str, Any]) -> str:
    sym = str(item.get("symbol") or "").upper().strip()
    title = str(item.get("title") or "")[:64].strip().lower()
    return f"{sym}::{title}"


def parse_news_timestamp(item: Dict[str, Any]) -> Optional[datetime]:
    """Best-effort parse of published/timestamp fields on a news row."""
    for key in (
        "published", "publish_date", "published_at", "timestamp", "date", "datetime",
        "first_seen_at", "provider_received_at", "cycle_detected_at",
    ):
        raw = item.get(key)
        if raw is None or raw == "":
            continue
        if isinstance(raw, datetime):
            return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        if isinstance(raw, (int, float)):
            try:
                ts = float(raw)
                if ts > 1e12:
                    ts /= 1000.0
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except (OSError, OverflowError, ValueError):
                continue
        text = str(raw).strip()
        if not text:
            continue
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
        for fmt in (
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                cleaned = text
                if fmt.endswith("%z") and cleaned.endswith("Z"):
                    cleaned = cleaned[:-1] + "+0000"
                dt = datetime.strptime(cleaned[:32], fmt)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def classify_news_freshness(item: Dict[str, Any], config: ConfigLike = None) -> str:
    """BREAKING | INTRADAY | RECENT_CATALYST | BACKGROUND | STALE | UNKNOWN."""
    cfg = news_pipeline_config(config)
    classes = cfg.get("freshness_classes") or _DEFAULT_PIPELINE["freshness_classes"]
    dt = parse_news_timestamp(item)
    if dt is None:
        return "UNKNOWN"
    now = datetime.now(timezone.utc)
    try:
        age_h = (now - dt.astimezone(timezone.utc)).total_seconds() / 3600.0
    except Exception:
        return "UNKNOWN"
    if age_h <= float(classes.get("BREAKING", 2)):
        return "BREAKING"
    if age_h <= float(classes.get("INTRADAY", 18)):
        return "INTRADAY"
    if age_h <= float(classes.get("RECENT_CATALYST", 72)):
        return "RECENT_CATALYST"
    if age_h <= float(classes.get("BACKGROUND", 168)):
        return "BACKGROUND"
    return "STALE"


def freshness_confidence_multiplier(freshness_class: str, *, day_trade: bool = False) -> float:
    """Day-trade scanners ignore BACKGROUND for confidence."""
    if day_trade:
        return {
            "BREAKING": 1.0,
            "INTRADAY": 0.9,
            "RECENT_CATALYST": 0.55,
            "BACKGROUND": 0.0,
            "STALE": 0.0,
            "UNKNOWN": 0.4,
        }.get(freshness_class, 0.4)
    return {
        "BREAKING": 1.0,
        "INTRADAY": 0.95,
        "RECENT_CATALYST": 0.75,
        "BACKGROUND": 0.35,
        "STALE": 0.0,
        "UNKNOWN": 0.5,
    }.get(freshness_class, 0.5)


def is_news_item_fresh(item: Dict[str, Any], max_age_days: int = 7) -> bool:
    """True if undated or within max_age_days. Drops clearly old headlines."""
    cls = classify_news_freshness(item)
    if cls == "STALE":
        return False
    dt = parse_news_timestamp(item)
    if dt is None:
        return True
    now = datetime.now(timezone.utc)
    try:
        age = now - dt.astimezone(timezone.utc)
    except Exception:
        return True
    return age <= timedelta(days=max(1, int(max_age_days)))


def event_fingerprint(item: Dict[str, Any]) -> str:
    """Cluster republished headlines into one underlying event."""
    title = str(item.get("title") or "").lower()
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    for prefix in ("breaking:", "update:", "exclusive:", "just in:"):
        if title.startswith(prefix):
            title = title[len(prefix):].strip()
    companies = []
    for key in ("symbol", "company_name"):
        val = str(item.get(key) or "").upper().strip()
        if val:
            companies.append(val)
    numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", title)
    dt = parse_news_timestamp(item)
    day = dt.astimezone(timezone.utc).strftime("%Y-%m-%d") if dt else "nodate"
    raw = "|".join([title[:80], ",".join(sorted(set(companies))), ",".join(numbers[:4]), day])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def dedupe_news_events(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse republished copies; keep first as original, mark rest as repost."""
    clusters: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        fp = event_fingerprint(row)
        row["event_fingerprint"] = fp
        row["freshness_class"] = classify_news_freshness(row)
        if "cycle_detected_at" not in row:
            row["cycle_detected_at"] = datetime.now(timezone.utc).isoformat()
        if fp not in clusters:
            row["event_role"] = "original"
            row["repost_count"] = 0
            clusters[fp] = row
            order.append(fp)
        else:
            clusters[fp]["repost_count"] = int(clusters[fp].get("repost_count") or 0) + 1
            src_a = str(clusters[fp].get("source") or "").lower()
            src_b = str(row.get("source") or "").lower()
            if src_b and src_b != src_a:
                conf = list(clusters[fp].get("confirming_sources") or [])
                if src_b not in conf:
                    conf.append(src_b)
                clusters[fp]["confirming_sources"] = conf
    return [clusters[fp] for fp in order]


def filter_fresh_news(
    items: List[Dict[str, Any]],
    *,
    max_age_days: int = 7,
) -> List[Dict[str, Any]]:
    """Drop parseably-stale articles; stamp freshness; dedupe republishes."""
    kept: List[Dict[str, Any]] = []
    dropped = 0
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if is_news_item_fresh(item, max_age_days=max_age_days):
            row = dict(item)
            row["freshness_class"] = classify_news_freshness(row)
            kept.append(row)
        else:
            dropped += 1
    if dropped:
        print(f"[NEWS] Freshness filter dropped {dropped} stale items")
    return dedupe_news_events(kept)


def score_news_potential(item: Dict[str, Any]) -> float:
    """Heuristic for deep-investigate ranking."""
    score = 0.0
    try:
        score += float(item.get("catalyst_score") or 0) * 0.4
    except (TypeError, ValueError):
        pass
    try:
        score += abs(float(item.get("sentiment") or 0)) * 0.2
    except (TypeError, ValueError):
        pass
    if item.get("symbol"):
        score += 0.2
    fc = classify_news_freshness(item)
    score += {
        "BREAKING": 0.35,
        "INTRADAY": 0.25,
        "RECENT_CATALYST": 0.1,
        "BACKGROUND": 0.0,
    }.get(fc, 0.05)
    if item.get("confirming_sources"):
        score += min(0.2, 0.05 * len(item["confirming_sources"]))
    return min(1.0, score)


def merge_cycle_news_items(
    cycle_data,
    priority_items: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Flatten typed cycle snapshots into a news-item list for legacy callers."""
    if cycle_data is None and not priority_items:
        return []
    items: List[Dict[str, Any]] = []
    if cycle_data is not None:
        for bucket_name in ("news_events", "sec_events", "social_events", "ingested_news"):
            bucket = getattr(cycle_data, bucket_name, None) or []
            for item in bucket:
                if isinstance(item, dict):
                    items.append(dict(item))
    for item in priority_items or []:
        if isinstance(item, dict):
            items.append(dict(item))
    return dedupe_news_events(items)


async def fetch_article_body(url: str, timeout: float = 8.0) -> str:
    """Best-effort article body extract for top events (not headlines only)."""
    if not url or not str(url).startswith("http"):
        return ""
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 PhasmaAI/1.0"},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = " ".join(p for p in paragraphs if len(p) > 40)
        return text[:4000]
    except Exception:
        return ""


async def deep_investigate_high_potential(
    news_engine,
    items: List[Dict[str, Any]],
    *,
    config: ConfigLike,
) -> List[Dict[str, Any]]:
    """Targeted supplemental fetch for a few high-potential symbols — not a full news cycle."""
    cfg = news_pipeline_config(config)
    if not cfg.get("deep_investigate_enabled", True):
        return []

    max_items = int(cfg.get("deep_investigate_max_items", 3))
    min_score = float(cfg.get("deep_investigate_min_score", 0.55))

    ranked: List[tuple] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sym = str(item.get("symbol") or "").upper().strip()
        if not sym or sym.startswith("KX"):
            continue
        if classify_news_freshness(item) in ("BACKGROUND", "STALE"):
            continue
        pot = score_news_potential(item)
        if pot >= min_score:
            ranked.append((pot, sym, item))

    ranked.sort(key=lambda row: row[0], reverse=True)
    symbols: List[str] = []
    seen_syms: set = set()
    top_items: List[Dict[str, Any]] = []
    for pot, sym, item in ranked:
        if sym in seen_syms:
            continue
        seen_syms.add(sym)
        symbols.append(sym)
        top_items.append(item)
        if len(symbols) >= max_items:
            break

    if not symbols:
        return []

    print(
        f"\n🔬 Deep news investigation: {len(symbols)} high-potential symbols "
        f"({', '.join(symbols)}) — body extract + targeted lines"
    )

    supplemental: List[Dict[str, Any]] = []
    seen_keys: set = {news_item_key(i) for i in items if isinstance(i, dict)}

    for item in top_items[:max_items]:
        url = str(item.get("url") or "")
        if not url:
            continue
        body = await fetch_article_body(url)
        if body:
            row = dict(item)
            row["article_body"] = body
            row["deep_investigation"] = True
            row["summary"] = (str(row.get("summary") or "") + " | " + body[:400]).strip(" |")
            try:
                from utils.company_identity_registry import get_identity_registry
                get_identity_registry().stamp_item(row)
            except Exception:
                pass
            key = news_item_key(row) + "::body"
            if key not in seen_keys:
                seen_keys.add(key)
                supplemental.append(row)

    apis = getattr(news_engine, "apis", None)
    if apis is not None:
        for sym in symbols:
            try:
                rows = await apis.scan_yahoo_rss([sym])
                for row in rows or []:
                    if not isinstance(row, dict):
                        continue
                    row = dict(row)
                    row["source"] = row.get("source") or "deep_investigation"
                    row["deep_investigation"] = True
                    try:
                        from utils.company_identity_registry import get_identity_registry
                        get_identity_registry().stamp_item(row)
                        get_identity_registry().remember(
                            sym,
                            company_name=row.get("company_name"),
                            source="yahoo_rss",
                        )
                    except Exception:
                        pass
                    key = news_item_key(row)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    supplemental.append(row)
            except Exception as exc:
                print(f"   ⚠️ Deep investigation fetch failed for {sym}: {exc}")

    if supplemental:
        print(f"   ✅ Added {len(supplemental)} supplemental articles from follow-up fetch")
    return supplemental
