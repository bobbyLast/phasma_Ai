"""Shared engine inventory analysis — classification, references, deduping."""

from __future__ import annotations

import ast
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Group inference (extended) ---
GROUP_MAP = {
    "ingest": "IngestGroup",
    "news": "IngestGroup",
    "rss": "IngestGroup",
    "cycle_data": "IngestGroup",
    "market": "MarketGroup",
    "cache": "MarketGroup",
    "fred": "MarketGroup",
    "regime": "MarketGroup",
    "price_fetch": "MarketGroup",
    "crash": "RiskGroup",
    "macro": "RiskGroup",
    "risk": "RiskGroup",
    "defensive": "RiskGroup",
    "discovery": "DiscoveryGroup",
    "universal": "DiscoveryGroup",
    "bull": "DiscoveryGroup",
    "social": "DiscoveryGroup",
    "partnership": "DiscoveryGroup",
    "underground": "DiscoveryGroup",
    "thematic": "DiscoveryGroup",
    "sector": "DiscoveryGroup",
    "insider": "DiscoveryGroup",
    "politician": "DiscoveryGroup",
    "geo": "DiscoveryGroup",
    "kalshi": "DiscoveryGroup",
    "convergence": "DiscoveryGroup",
    "pump": "DiscoveryGroup",
    "whale": "DiscoveryGroup",
    "resolver": "EnrichmentGroup",
    "validation": "EnrichmentGroup",
    "enrich": "EnrichmentGroup",
    "fact_check": "EnrichmentGroup",
    "company": "EnrichmentGroup",
    "monte": "SignalGroup",
    "simulation": "SignalGroup",
    "sim_": "SignalGroup",
    "options": "SignalGroup",
    "signal": "SignalGroup",
    "decision": "DecisionGroup",
    "confluence": "DecisionGroup",
    "jury": "DecisionGroup",
    "gate": "DecisionGroup",
    "strategy_router": "DecisionGroup",
    "execution": "ExecutionGroup",
    "paper": "ExecutionGroup",
    "broker": "ExecutionGroup",
    "alpaca": "ExecutionGroup",
    "trade_memory": "ExecutionGroup",
    "telegram": "ReportingGroup",
    "gallery": "ReportingGroup",
    "report": "ReportingGroup",
    "digest": "ReportingGroup",
    "outcome": "LearningGroup",
    "grader": "LearningGroup",
    "exit": "LearningGroup",
    "learning": "LearningGroup",
    "portfolio": "LearningGroup",
    "ledger": "LearningGroup",
}

MAIN_PATH_MARKERS = (
    "run_full_cycle",
    "run_continuous",
    "_stage_",
    "worker_supervisor",
    "group_coordinator",
    "ExecutionRouter",
    "DecisionPipeline",
)

HIGH_RISK_KEYWORDS = (
    "execution", "paper_trading", "live_trading", "broker", "alpaca",
    "telegram", "trade_memory", "outcome_grader", "grader", "data_gate",
    "approval", "jury", "confluence", "position_siz", "submit_signal",
)

REPLACEMENT_HINTS: List[Tuple[str, str, str]] = [
    (r"market_crash_detector[^_]", "engines/market_crash_detector_v2.py", "MarketCrashDetectorV2"),
    (r"crash_detector\.py", "engines/market_crash_detector_v2.py", "v2 crash detector"),
    (r"enhanced_alpaca|alpaca_paper_trader", "core/execution/execution_router.py", "ExecutionRouter"),
    (r"real_portfolio_manager|paper_portfolio", "engines/real_portfolio_manager.py", "local ledger path"),
    (r"FILTERED_FUNNEL|filtered_funnel", "core/signals/decision_pipeline.py", "DecisionPipeline"),
    (r"meta_brain\.py", "brain/unified_meta_brain.py", "UnifiedMetaBrain"),
    (r"signal_scorer|enhanced_confluence", "core/signals/decision_pipeline.py", "DecisionGroup"),
]

UTILITY_NAME_RE = re.compile(
    r"^(get_|set_|format_|normalize_|parse_|build_|load_|save_|is_|has_|to_|from_|"
    r"compute_|calculate_|validate_|merge_|filter_|extract_|render_|print_|log_|"
    r"create_|update_|fetch_|read_|write_|handle_|wrap_|make_|ensure_|check_)",
    re.I,
)

UTILITY_CLASS_SUFFIX = re.compile(
    r"(Config|Settings|Params|Parameters|Result|Results|Context|State|Record|"
    r"Summary|Metrics|Stats|Helper|Utils|Adapter|Formatter|Serializer|Exception|Error)$",
    re.I,
)

DEMO_PATTERNS = re.compile(
    r"(demo|sample|fake|mock|placeholder|diagnostic|legacy/|alternate_mains|"
    r"FILTERED_FUNNEL|filter_demo|test_mode|using_demo)",
    re.I,
)

DYNAMIC_PATTERNS = re.compile(
    r"(getattr\s*\(|importlib\.|__import__\s*\(|globals\s*\(\)|locals\s*\(\)|"
    r"eval\s*\(|exec\s*\(|registry|plugin|factory|load_class|dynamic)",
    re.I,
)

STAGE_BANNER_RE = re.compile(
    r"(PHASE|STAGE|GROUP HEALTH|RUNTIME PROFILE|WORKER HEALTH|DECISION SUMMARY|"
    r"UNIFIED META BRAIN|INGEST|ANALYZE|SYNTHESIZE|EXECUTION_SKIPPED)",
    re.I,
)

CODE_BANNER_RE = re.compile(
    r"(^\s*(def |class |import |from |if |for |return |elif |else:|getattr|"
    r"await |async def |self\.|print\(f?[\"']?\s*[📊🎯✅❌⏭️]))",
    re.I,
)

IMPORT_BANNER_RE = re.compile(r"^\s*(from\s+\S+\s+import|import\s+\S+)", re.I)

PATH_PREFIX_GROUP = [
    ("core/execution/", "ExecutionGroup"),
    ("core/signals/", "DecisionGroup"),
    ("core/supervisor/", "ReportingGroup"),
    ("core/monitoring/", "ReportingGroup"),
    ("core/runtime/", "Utility"),
    ("engines/long_tier/", "EnrichmentGroup"),
    ("engines/sports_odds", "DiscoveryGroup"),
    ("engines/kalshi", "DiscoveryGroup"),
    ("engines/news", "IngestGroup"),
    ("engines/market_crash", "RiskGroup"),
    ("engines/market_regime", "MarketGroup"),
    ("engines/monte_carlo", "SignalGroup"),
    ("engines/options", "SignalGroup"),
    ("engines/alpaca", "ExecutionGroup"),
    ("engines/paper", "ExecutionGroup"),
    ("engines/real_portfolio", "LearningGroup"),
    ("engines/underground", "DiscoveryGroup"),
    ("engines/pump", "DiscoveryGroup"),
    ("engines/insider", "DiscoveryGroup"),
    ("engines/social", "DiscoveryGroup"),
    ("engines/sector", "DiscoveryGroup"),
    ("engines/global_macro", "RiskGroup"),
    ("engines/risk", "RiskGroup"),
    ("engines/exit", "LearningGroup"),
    ("engines/outcome", "LearningGroup"),
    ("brain/", "DiscoveryGroup"),
    ("utils/telegram", "ReportingGroup"),
    ("utils/portfolio", "LearningGroup"),
    ("utils/trade_memory", "ExecutionGroup"),
    ("utils/confidence", "Utility"),
    ("utils/signal", "Utility"),
    ("utils/company_resolver", "EnrichmentGroup"),
    ("scripts/ops/telegram", "ReportingGroup"),
]


def infer_group(name: str, path: str) -> str:
    text = f"{name} {path}".lower()
    for prefix, group in PATH_PREFIX_GROUP:
        if path.replace("\\", "/").startswith(prefix) or prefix.rstrip("/") in path.replace("\\", "/"):
            return group
    for key, group in GROUP_MAP.items():
        if key in text:
            return group
    return "Unmapped"


def infer_group_from_path(path: str) -> str:
    p = path.replace("\\", "/")
    for prefix, group in PATH_PREFIX_GROUP:
        if p.startswith(prefix) or prefix.rstrip("/") in p:
            return group
    if p.startswith("utils/"):
        return "Utility"
    if p.startswith("scripts/"):
        return "Utility"
    if p == "main.py":
        return "ReportingGroup"
    return "Unmapped"


def normalize_symbol(name: str) -> str:
    """Canonical key for deduping banners/classes/functions."""
    n = name.strip()
    if IMPORT_BANNER_RE.match(n):
        m = re.search(r"import\s+(\w+)", n)
        if m:
            return m.group(1).lower()
        m = re.search(r"from\s+[\w.]+\s+import\s+([\w,\s]+)", n)
        if m:
            parts = [p.strip().lower() for p in m.group(1).split(",") if p.strip()]
            return parts[0] if parts else n.lower()[:60]
    n = re.sub(r"[^\w]+", "_", n).strip("_").lower()
    return n[:80]


def is_import_banner(name: str, category: str) -> bool:
    if category == "banner" and IMPORT_BANNER_RE.match(name.strip()):
        return True
    return False


def is_logical_engine(entry: Dict[str, Any]) -> bool:
    """True if item should count as engine/stage, not utility noise."""
    name = str(entry.get("name") or "")
    path = str(entry.get("file_path") or "")
    category = str(entry.get("category") or "")
    classification = entry.get("triage_classification") or entry.get("classification")

    if classification in (
        "UTILITY_NOT_ENGINE", "DUPLICATE_ALIAS", "TEST_ONLY", "DEMO_ONLY",
    ):
        return False
    if is_import_banner(name, category):
        return False
    if path.startswith("tests/") or "/tests/" in path:
        return False
    if "scripts/legacy" in path or "scripts/alternate_mains" in path:
        return False
    if category == "function" and UTILITY_NAME_RE.match(name):
        return False
    if category == "class" and UTILITY_CLASS_SUFFIX.search(name):
        # Engine-named classes still count
        if not re.search(
            r"(Engine|Detector|Scanner|Monitor|Worker|Brain|Intelligence|Router|Guard|Jury|Grader)",
            name,
            re.I,
        ):
            return False
    if category == "banner":
        # Code-line banners that aren't stage headings
        if name.startswith(("def ", "class ", "if ", "for ", "return ", "#")):
            return False
        if len(name) > 100 and "import" in name:
            return False
    return True


class ReferenceIndex:
    """Pre-built cross-reference index for the codebase."""

    def __init__(self, root: str = ROOT):
        self.root = root
        self.file_sources: Dict[str, str] = {}
        self.symbol_refs: Dict[str, Set[str]] = defaultdict(set)
        self.path_refs: Dict[str, Set[str]] = defaultdict(set)
        self.dynamic_refs: Dict[str, Set[str]] = defaultdict(set)
        self.main_refs: Dict[str, Set[str]] = defaultdict(set)
        self.supervisor_refs: Dict[str, Set[str]] = defaultdict(set)
        self.coordinator_refs: Dict[str, Set[str]] = defaultdict(set)
        self.config_refs: Dict[str, Set[str]] = defaultdict(set)
        self.test_refs: Dict[str, Set[str]] = defaultdict(set)
        self._build()

    def _iter_py_files(self) -> List[str]:
        out = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in (
                ".git", "__pycache__", "node_modules", ".venv", "venv", "archive",
            )]
            for fn in filenames:
                if fn.endswith(".py"):
                    out.append(os.path.join(dirpath, fn))
        return out

    def _rel(self, path: str) -> str:
        return os.path.relpath(path, self.root).replace("\\", "/")

    def _build(self) -> None:
        anchor_files = {
            "main": os.path.join(self.root, "main.py"),
            "coordinator": os.path.join(self.root, "core/supervisor/group_coordinator.py"),
            "supervisor": os.path.join(self.root, "core/supervisor/supervisor.py"),
            "workers": os.path.join(self.root, "core/supervisor/workers.py"),
        }
        anchor_content = {}
        for key, fp in anchor_files.items():
            if os.path.isfile(fp):
                try:
                    anchor_content[key] = open(fp, encoding="utf-8", errors="replace").read()
                except Exception:
                    anchor_content[key] = ""

        config_text = ""
        cfg_path = os.path.join(self.root, "config.json")
        if os.path.isfile(cfg_path):
            try:
                config_text = open(cfg_path, encoding="utf-8").read()
            except Exception:
                pass

        for fp in self._iter_py_files():
            rel = self._rel(fp)
            try:
                source = open(fp, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            self.file_sources[rel] = source
            is_test = rel.startswith("tests/") or "/tests/" in rel

            # AST imports
            try:
                tree = ast.parse(source, filename=fp)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            mod = alias.name
                            sym = alias.asname or mod.split(".")[-1]
                            self.symbol_refs[sym.lower()].add(rel)
                            self.path_refs[mod.replace(".", "/")].add(rel)
                    elif isinstance(node, ast.ImportFrom):
                        mod = node.module or ""
                        for alias in node.names:
                            sym = alias.name
                            self.symbol_refs[sym.lower()].add(rel)
                            if mod:
                                self.path_refs[f"{mod.replace('.', '/')}/{sym}"].add(rel)
            except Exception:
                pass

            # String references for classes/functions
            for m in re.finditer(r"\b([A-Z][A-Za-z0-9_]*)\b", source):
                self.symbol_refs[m.group(1).lower()].add(rel)

            if DYNAMIC_PATTERNS.search(source):
                for m in re.finditer(r'["\']([A-Za-z_][A-Za-z0-9_]*)["\']', source):
                    self.dynamic_refs[m.group(1).lower()].add(rel)

            def _match_anchor(text: str, store: Dict[str, Set[str]]) -> None:
                for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", source):
                    if token in text:
                        store[token.lower()].add(rel)

            if "main.py" in rel:
                pass
            elif is_test:
                for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", source):
                    self.test_refs[token.lower()].add(rel)
            else:
                pass  # anchor cross-refs handled in references_for via direct main text search

            if config_text:
                for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", source):
                    if token.lower() in config_text.lower():
                        self.config_refs[token.lower()].add(rel)

    def references_for(self, entry: Dict[str, Any]) -> Dict[str, List[str]]:
        name = str(entry.get("name") or "")
        path = str(entry.get("file_path") or "")
        symbols = set()

        # Extract symbols from name
        if IMPORT_BANNER_RE.match(name.strip()):
            for m in re.finditer(r"\b([A-Z][A-Za-z0-9_]*)\b", name):
                symbols.add(m.group(1).lower())
        else:
            symbols.add(normalize_symbol(name))
            for part in re.findall(r"[A-Z][a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|[A-Z]+", name):
                symbols.add(part.lower())

        base = os.path.basename(path).replace(".py", "").lower()
        symbols.add(base)

        imported_by: Set[str] = set()
        callers: Set[str] = set()
        for sym in symbols:
            if sym:
                for ref in self.symbol_refs.get(sym, set()):
                    if ref != path:
                        imported_by.add(ref)
                for ref in self.path_refs.get(sym, set()):
                    if ref != path:
                        imported_by.add(ref)

        for sym in symbols:
            for ref in self.main_refs.get(sym, set()):
                if ref == path:
                    callers.add("main.py (anchor match)")
            for ref in self.supervisor_refs.get(sym, set()):
                if ref == path:
                    callers.add(f"{ref} (supervisor/worker path)")
            for ref in self.coordinator_refs.get(sym, set()):
                if ref == path:
                    callers.add("group_coordinator.py")

        # Direct text search in anchor files for symbol (strict: whole-word-ish)
        for sym in symbols:
            if len(sym) < 4:
                continue
            for label, content in (
                ("main.py", self.file_sources.get("main.py", "")),
                ("group_coordinator.py", self.file_sources.get("core/supervisor/group_coordinator.py", "")),
                ("supervisor.py", self.file_sources.get("core/supervisor/supervisor.py", "")),
                ("workers.py", self.file_sources.get("core/supervisor/workers.py", "")),
            ):
                if not content:
                    continue
                if re.search(rf"\b{re.escape(sym)}\b", content, re.I):
                    callers.add(label)

        test_hits = set()
        for sym in symbols:
            test_hits.update(self.test_refs.get(sym, set()))

        config_hits = set()
        for sym in symbols:
            config_hits.update(self.config_refs.get(sym, set()))

        dynamic = set()
        for sym in symbols:
            dynamic.update(self.dynamic_refs.get(sym, set()))

        log_evidence: List[str] = []
        log_dirs = [
            os.path.join(self.root, "data", "runtime", "logs"),
            os.path.join(self.root, "data", "runtime"),
            self.root,
        ]
        needle = name[:60] if len(name) > 10 else None
        if needle:
            for d in log_dirs:
                if not os.path.isdir(d):
                    continue
                for fn in os.listdir(d)[:30]:
                    if not fn.endswith((".log", ".txt")):
                        continue
                    fp = os.path.join(d, fn)
                    try:
                        with open(fp, encoding="utf-8", errors="replace") as f:
                            for line in f:
                                if needle.lower() in line.lower():
                                    log_evidence.append(f"{fn}: {line.strip()[:100]}")
                                    if len(log_evidence) >= 3:
                                        break
                    except Exception:
                        pass
                    if len(log_evidence) >= 3:
                        break

        return {
            "imported_by": sorted(imported_by)[:20],
            "callers": sorted(callers)[:15],
            "references_from_main": [c for c in callers if "main" in c],
            "references_from_group_coordinator": [c for c in callers if "coordinator" in c],
            "references_from_supervisor": [c for c in callers if "supervisor" in c or "worker" in c.lower()],
            "references_from_config": sorted(config_hits)[:10],
            "references_from_tests": sorted(test_hits)[:15],
            "dynamic_call_evidence": sorted(dynamic)[:10],
            "runtime_log_evidence": log_evidence[:3],
        }


_git_cache: Dict[str, Dict[str, str]] = {}
_mtime_cache: Dict[str, str] = {}


def git_info(file_path: str) -> Dict[str, str]:
    if file_path in _git_cache:
        return _git_cache[file_path]
    info = {"last_commit": "", "last_commit_date": ""}
    full = os.path.join(ROOT, file_path) if not os.path.isabs(file_path) else file_path
    if os.path.isfile(full):
        try:
            info["last_modified"] = datetime.fromtimestamp(
                os.path.getmtime(full), tz=timezone.utc,
            ).isoformat()
        except Exception:
            info["last_modified"] = ""
        try:
            r = subprocess.run(
                ["git", "log", "-1", "--format=%h %s|%ci", "--", file_path],
                cwd=ROOT, capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                parts = r.stdout.strip().split("|", 1)
                info["last_commit"] = parts[0]
                info["last_commit_date"] = parts[1] if len(parts) > 1 else ""
        except Exception:
            pass
    _git_cache[file_path] = info
    return info


def extract_docstring(file_path: str, line: Optional[int], name: str) -> str:
    full = os.path.join(ROOT, file_path)
    if not os.path.isfile(full) or not line:
        return ""
    try:
        source = open(full, encoding="utf-8", errors="replace").read()
        tree = ast.parse(source, filename=full)
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == name.split(",")[0].strip()[:80]:
                doc = ast.get_docstring(node) or ""
                return doc.split("\n")[0][:200]
            if isinstance(node, ast.ClassDef) and node.lineno == line:
                doc = ast.get_docstring(node) or ""
                return doc.split("\n")[0][:200]
            if isinstance(node, ast.FunctionDef) and node.lineno == line:
                doc = ast.get_docstring(node) or ""
                return doc.split("\n")[0][:200]
    except Exception:
        pass
    return ""


def find_replacement(name: str, path: str) -> Optional[Dict[str, str]]:
    text = f"{name} {path}"
    for pattern, new_path, reason in REPLACEMENT_HINTS:
        if re.search(pattern, text, re.I):
            return {"likely_replacement": new_path, "replacement_reason": reason}
    if "_v2" not in path and "detector" in path.lower():
        v2 = path.replace(".py", "_v2.py")
        if os.path.isfile(os.path.join(ROOT, v2)):
            return {"likely_replacement": v2, "replacement_reason": "v2 module exists alongside v1"}
    return None


def classify_entry(
    entry: Dict[str, Any],
    refs: ReferenceIndex,
    canonical_map: Dict[str, str],
) -> Dict[str, Any]:
    """Return triage record for one inventory entry."""
    name = str(entry.get("name") or "")
    path = str(entry.get("file_path") or "")
    category = str(entry.get("category") or "")
    norm = normalize_symbol(name)
    eid = entry.get("engine_id", "")

    ref_data = refs.references_for(entry)
    imported_by = ref_data["imported_by"]
    callers = ref_data["callers"]
    test_refs = ref_data["references_from_tests"]
    main_refs = ref_data["references_from_main"]
    git = git_info(path) if path and not path.startswith("log_") else {}

    replacement = find_replacement(name, path)
    closest_group = infer_group(name, path)
    if closest_group == "Unmapped":
        # try path-only
        closest_group = infer_group(os.path.basename(path), path)

    doc = extract_docstring(path, entry.get("line"), name)

    # --- Classification rules (ordered priority) ---
    classification = "UNKNOWN_NEEDS_REVIEW"
    confidence = 0.5
    recommended_action = "MANUAL_REVIEW"
    assigned_group = entry.get("recommended_group") or "Unmapped"

    is_high_risk = any(k in f"{name} {path}".lower() for k in HIGH_RISK_KEYWORDS)

    # Log-scanned banners are runtime noise, not executable engines
    if entry.get("discovered_by") == "log_scan" or str(eid).startswith("log_banner:"):
        classification = "UTILITY_NOT_ENGINE"
        confidence = 0.95
        recommended_action = "Remove from engine count (log banner, not engine)"
        assigned_group = "Utility"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if "scripts/legacy/live_trading_cycle.py" in path.replace("\\", "/"):
        classification = "DEMO_ONLY"
        confidence = 0.95
        recommended_action = "QUARANTINE — legacy demo script, not in main path"
        assigned_group = "Deprecated"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    # Duplicate
    canon_id = canonical_map.get(norm)
    if canon_id and canon_id != eid and norm:
        classification = "DUPLICATE_ALIAS"
        confidence = 0.85
        recommended_action = "Merge into canonical engine_id"
        assigned_group = "Utility"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if path.startswith("tests/") or (test_refs and not imported_by and not callers):
        classification = "TEST_ONLY"
        confidence = 0.9
        recommended_action = "Exclude from production engine count"
        assigned_group = "TestOnly"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if DEMO_PATTERNS.search(f"{name} {path}") or "demo" in name.lower():
        classification = "DEMO_ONLY"
        confidence = 0.88
        recommended_action = "KEEP diagnostics only — block from DecisionGroup"
        assigned_group = "DemoOnly"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if path == "main.py" and category == "banner":
        stripped = name.strip()
        if stripped.startswith("#") and not STAGE_BANNER_RE.search(name):
            classification = "UTILITY_NOT_ENGINE"
            confidence = 0.9
            recommended_action = "Remove from engine count (comment banner)"
            assigned_group = "Utility"
            return _record(
                entry, ref_data, git, doc, closest_group, replacement,
                classification, confidence, recommended_action, assigned_group, is_high_risk,
            )
        if CODE_BANNER_RE.search(name) or (stripped.startswith("print(") and not STAGE_BANNER_RE.search(name)):
            classification = "UTILITY_NOT_ENGINE"
            confidence = 0.88
            recommended_action = "Remove from engine count (main.py code/log banner)"
            assigned_group = "Utility"
            return _record(
                entry, ref_data, git, doc, closest_group, replacement,
                classification, confidence, recommended_action, assigned_group, is_high_risk,
            )
        if STAGE_BANNER_RE.search(name):
            classification = "ACTIVE_CURRENT"
            confidence = 0.75
            recommended_action = "MAP_TO_GROUP"
            assigned_group = infer_group(name, path)
            if assigned_group == "Unmapped":
                assigned_group = "ReportingGroup"
            return _record(
                entry, ref_data, git, doc, closest_group, replacement,
                classification, confidence, recommended_action, assigned_group, is_high_risk,
            )

    if path == "main.py" and category == "function" and UTILITY_NAME_RE.match(name):
        classification = "UTILITY_NOT_ENGINE"
        confidence = 0.85
        recommended_action = "Remove from engine count (main helper)"
        assigned_group = "Utility"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if is_import_banner(name, category):
        classification = "UTILITY_NOT_ENGINE"
        confidence = 0.92
        recommended_action = "Remove from engine count (import line banner)"
        assigned_group = "Utility"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if category == "function" and UTILITY_NAME_RE.match(name):
        classification = "UTILITY_NOT_ENGINE"
        confidence = 0.8
        recommended_action = "Remove from engine count"
        assigned_group = "Utility"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if "scripts/legacy" in path or "scripts/alternate_mains" in path or "archive/" in path:
        classification = "ACTIVE_LEGACY"
        confidence = 0.75
        recommended_action = "DEPRECATE — legacy script path"
        assigned_group = "Deprecated"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if replacement and not imported_by and not callers:
        classification = "REPLACED_BY_NEW_ENGINE"
        confidence = 0.78
        recommended_action = "DEPRECATE — use replacement module"
        assigned_group = "Deprecated"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    has_main = bool(main_refs) or any("main.py" in c for c in callers)
    has_supervisor = bool(ref_data["references_from_supervisor"]) or any(
        "supervisor" in x or "workers" in x for x in callers
    )
    has_coordinator = bool(ref_data["references_from_group_coordinator"])
    has_dynamic = bool(ref_data["dynamic_call_evidence"])
    ref_count = len(imported_by) + len(callers)

    if has_main or has_supervisor or has_coordinator:
        classification = "ACTIVE_CURRENT"
        confidence = 0.82 if has_main else 0.7
        recommended_action = "MAP_TO_GROUP"
        assigned_group = closest_group if closest_group != "Unmapped" else infer_group_from_path(path)
        if assigned_group == "Unmapped" and category == "class":
            assigned_group = infer_group(name, path)
        if assigned_group == "Unmapped":
            assigned_group = "Utility" if path.startswith("utils/") else "DiscoveryGroup"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if ref_count > 0 or has_dynamic:
        classification = "ACTIVE_LEGACY"
        confidence = 0.65
        recommended_action = "Flag for migration — still referenced but not main path"
        assigned_group = closest_group if closest_group != "Unmapped" else infer_group_from_path(path)
        if assigned_group == "Unmapped":
            assigned_group = "Unknown"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if replacement:
        classification = "REPLACED_BY_NEW_ENGINE"
        confidence = 0.72
        recommended_action = "QUARANTINE candidate — likely superseded"
        assigned_group = "Deprecated"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    if ref_count == 0 and not ref_data["runtime_log_evidence"]:
        classification = "ORPHANED_UNCALLED"
        confidence = 0.7
        recommended_action = "QUARANTINE — no references found"
        assigned_group = "Deprecated"
        return _record(
            entry, ref_data, git, doc, closest_group, replacement,
            classification, confidence, recommended_action, assigned_group, is_high_risk,
        )

    classification = "UNKNOWN_NEEDS_REVIEW"
    confidence = 0.4
    recommended_action = "MANUAL_REVIEW"
    assigned_group = "Unknown"
    return _record(
        entry, ref_data, git, doc, closest_group, replacement,
        classification, confidence, recommended_action, assigned_group, is_high_risk,
    )


def _record(
    entry, ref_data, git, doc, closest_group, replacement,
    classification, confidence, recommended_action, assigned_group, is_high_risk,
) -> Dict[str, Any]:
    return {
        "engine_id": entry.get("engine_id"),
        "name": entry.get("name"),
        "file_path": entry.get("file_path"),
        "line": entry.get("line"),
        "discovered_by": entry.get("discovered_by"),
        "category": entry.get("category"),
        "class_or_function": entry.get("name"),
        "docstring_summary": doc,
        "imported_by": ref_data["imported_by"],
        "callers": ref_data["callers"],
        "references_from_main": ref_data["references_from_main"],
        "references_from_group_coordinator": ref_data["references_from_group_coordinator"],
        "references_from_supervisor": ref_data["references_from_supervisor"],
        "references_from_config": ref_data["references_from_config"],
        "references_from_tests": ref_data["references_from_tests"],
        "dynamic_call_evidence": ref_data["dynamic_call_evidence"],
        "runtime_log_evidence": ref_data["runtime_log_evidence"],
        "last_git_commit": git.get("last_commit", ""),
        "last_commit_date": git.get("last_commit_date", ""),
        "last_modified": git.get("last_modified", ""),
        "likely_purpose": doc or entry.get("category", ""),
        "closest_mapped_group": closest_group,
        "possible_replacement": (replacement or {}).get("likely_replacement", ""),
        "replacement_reason": (replacement or {}).get("replacement_reason", ""),
        "classification": classification,
        "confidence": confidence,
        "recommended_action": recommended_action,
        "assigned_group": assigned_group,
        "high_risk": is_high_risk,
    }


def build_canonical_map(entries: List[Dict[str, Any]]) -> Dict[str, str]:
    """First mapped entry per normalized symbol wins as canonical."""
    canon: Dict[str, str] = {}
    # Prefer known mapped groups
    sorted_entries = sorted(
        entries,
        key=lambda e: (0 if e.get("recommended_group") not in (None, "Unmapped") else 1, e.get("file_path", "")),
    )
    for e in sorted_entries:
        norm = normalize_symbol(str(e.get("name", "")))
        if norm and norm not in canon:
            canon[norm] = e.get("engine_id", "")
    return canon


def compute_dedup_summary(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    raw = len(entries)
    banners = set()
    symbols = set()
    logical = []
    utilities = 0
    duplicates = 0
    for e in entries:
        name = str(e.get("name", ""))
        if e.get("category") == "banner":
            banners.add(name[:120])
        symbols.add(normalize_symbol(name))
        cls = e.get("triage_classification") or e.get("classification")
        if cls == "UTILITY_NOT_ENGINE":
            utilities += 1
        elif cls == "DUPLICATE_ALIAS":
            duplicates += 1
        elif is_logical_engine(e):
            logical.append(e)
    return {
        "raw_items_found": raw,
        "unique_log_banners": len(banners),
        "unique_source_symbols": len(symbols),
        "unique_logical_engines": len(logical),
        "utilities_excluded": utilities,
        "duplicates_merged": duplicates,
        "unmapped_remaining": sum(
            1 for e in entries
            if e.get("recommended_group") == "Unmapped"
            and e.get("triage_classification") not in (
                "UTILITY_NOT_ENGINE", "DUPLICATE_ALIAS", "TEST_ONLY", "DEMO_ONLY",
                "ORPHANED_UNCALLED", "REPLACED_BY_NEW_ENGINE",
            )
        ),
    }
