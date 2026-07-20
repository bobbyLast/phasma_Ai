"""Brave Search grounding for prediction skills — LLM context with web-search fallback."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

_BRAVE_LLM_URL = "https://api.search.brave.com/res/v1/llm/context"
_BRAVE_WEB_URL = "https://api.search.brave.com/res/v1/web/search"
_DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
}
_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL = 3600
_HTML_TAG = re.compile(r"<[^>]+>")


def _clip(text: Any, limit: int = 200) -> str:
    raw = str(text or "").strip()
    raw = _HTML_TAG.sub(" ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    if len(raw) <= limit:
        return raw
    return raw[: max(0, limit - 3)].rstrip() + "..."


class BraveLLMContextClient:
    """Fetch compact grounding — prefers LLM Context, falls back to Web Search."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = dict(config or {})
        brave_cfg = cfg.get("brave") if isinstance(cfg.get("brave"), dict) else {}
        self.ai_key = os.getenv("BRAVE_AI_API_KEY", "").strip()
        self.search_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
        self.timeout = float(brave_cfg.get("timeout_seconds") or cfg.get("timeout_seconds") or 20)
        self.max_tokens = int(brave_cfg.get("maximum_number_of_tokens") or 2048)
        self.max_urls = int(brave_cfg.get("maximum_number_of_urls") or 3)
        self.count = int(brave_cfg.get("count") or 5)
        self.cache_ttl = int(brave_cfg.get("cache_ttl_seconds") or _CACHE_TTL)
        self.enabled = bool(cfg.get("enabled", True))
        self.allow_web_fallback = bool(brave_cfg.get("allow_web_fallback", True))

    @property
    def available(self) -> bool:
        return bool(self.enabled and (self.ai_key or self.search_key))

    @property
    def llm_context_available(self) -> bool:
        return bool(self.enabled and self.ai_key)

    def fetch_grounding(self, query: str) -> Dict[str, Any]:
        """Return compact grounding; tries LLM context then Brave web search."""
        q = str(query or "").strip()
        if not q:
            return {"snippets": [], "sources": [], "provider": "brave", "status": "empty_query"}
        if not self.available:
            return {"snippets": [], "sources": [], "provider": "brave", "status": "no_api_key"}

        cache_key = q.lower()[:160]
        cached = _CACHE.get(cache_key)
        if cached and (time.time() - cached.get("_ts", 0)) < self.cache_ttl:
            return dict(cached.get("payload") or {})

        payload: Dict[str, Any] = {"snippets": [], "sources": [], "provider": "brave", "status": "unavailable"}

        if self.ai_key:
            payload = self._fetch_llm_context(q)
            if payload.get("snippets"):
                _CACHE[cache_key] = {"_ts": time.time(), "payload": payload}
                return payload
            llm_status = payload.get("status", "")
            if llm_status == "ok":
                _CACHE[cache_key] = {"_ts": time.time(), "payload": payload}
                return payload
            logger.debug("Brave LLM context unavailable (%s) — trying web search fallback", llm_status)

        if self.allow_web_fallback and self.search_key:
            payload = self._fetch_web_search(q)
            _CACHE[cache_key] = {"_ts": time.time(), "payload": payload}
            return payload

        return payload

    def _fetch_llm_context(self, query: str) -> Dict[str, Any]:
        params = {
            "q": query,
            "count": self.count,
            "maximum_number_of_tokens": self.max_tokens,
            "maximum_number_of_urls": self.max_urls,
        }
        try:
            resp = requests.get(
                _BRAVE_LLM_URL,
                params=params,
                headers={**_DEFAULT_HEADERS, "X-Subscription-Token": self.ai_key},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.debug("Brave LLM context request failed: %s", exc)
            return {"snippets": [], "sources": [], "provider": "brave_context", "status": "request_error"}

        if resp.status_code != 200:
            detail = ""
            try:
                detail = str(((resp.json() or {}).get("error") or {}).get("code") or "")
            except Exception:
                pass
            status = detail or f"http_{resp.status_code}"
            logger.debug("Brave LLM context HTTP %s (%s)", resp.status_code, status)
            return {"snippets": [], "sources": [], "provider": "brave_context", "status": status}

        try:
            data = resp.json()
        except ValueError:
            return {"snippets": [], "sources": [], "provider": "brave_context", "status": "invalid_json"}

        return self._parse_llm_response(data)

    def _fetch_web_search(self, query: str) -> Dict[str, Any]:
        params = {"q": query, "count": min(self.count, self.max_urls)}
        try:
            resp = requests.get(
                _BRAVE_WEB_URL,
                params=params,
                headers={**_DEFAULT_HEADERS, "X-Subscription-Token": self.search_key},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.debug("Brave web search fallback failed: %s", exc)
            return {"snippets": [], "sources": [], "provider": "brave_web", "status": "request_error"}

        if resp.status_code != 200:
            return {
                "snippets": [],
                "sources": [],
                "provider": "brave_web",
                "status": f"http_{resp.status_code}",
            }

        try:
            data = resp.json()
        except ValueError:
            return {"snippets": [], "sources": [], "provider": "brave_web", "status": "invalid_json"}

        return self._parse_web_response(data)

    def _parse_llm_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        generic = (data.get("grounding") or {}).get("generic") or []
        snippets: List[str] = []
        sources: List[Dict[str, str]] = []
        for item in generic[: self.max_urls]:
            if not isinstance(item, dict):
                continue
            title = _clip(item.get("title") or "", 120)
            url = str(item.get("url") or "").strip()
            for snip in item.get("snippets") or []:
                text = _clip(snip, 240)
                if text:
                    snippets.append(text)
            if title or url:
                sources.append({"title": title, "url": url})
        return {
            "snippets": snippets[:5],
            "sources": sources[: self.max_urls],
            "provider": "brave_context",
            "status": "ok" if snippets else "no_snippets",
            "snippet_count": len(snippets),
        }

    def _parse_web_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        results = (data.get("web") or {}).get("results") or []
        snippets: List[str] = []
        sources: List[Dict[str, str]] = []
        for item in results[: self.max_urls]:
            if not isinstance(item, dict):
                continue
            title = _clip(item.get("title") or "", 120)
            url = str(item.get("url") or "").strip()
            desc = _clip(item.get("description") or "", 240)
            if desc:
                snippets.append(desc)
            elif title:
                snippets.append(title)
            if title or url:
                sources.append({"title": title, "url": url})
        return {
            "snippets": snippets[:5],
            "sources": sources[: self.max_urls],
            "provider": "brave_web",
            "status": "ok_web" if snippets else "no_snippets",
            "snippet_count": len(snippets),
        }
