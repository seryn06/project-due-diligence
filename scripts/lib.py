"""project-due-diligence 共享库：API 抓取/退避、归一化、JSON IO、运行区工具。stdlib only。"""
import json, os, re, tempfile, time, unicodedata, urllib.error, urllib.parse, urllib.request

UNIFIED_FIELDS = ["source", "source_id", "doi", "title", "year", "authors", "venue",
                  "abstract", "citation_count", "oa_url", "paper_type"]
PATHS = ["综述", "奠基", "前沿", "引文追踪", "反证"]
TIERS = {
    "快速": {"core_questions": 3, "min_included": 10, "min_reviews": 1, "l2_min": 5, "l3_min": 0, "min_gaps": 1},
    "标准": {"core_questions": 5, "min_included": 25, "min_reviews": 3, "l2_min": 10, "l3_min": 2, "min_gaps": 3},
    "深入": {"core_questions": 8, "min_included": 40, "min_reviews": 5, "l2_min": 20, "l3_min": 5, "min_gaps": 5},
}
REPORT_SECTIONS = ["Executive Summary", "项目分解", "文献检索协议（含覆盖限制）", "研究现状",
                   "痛点分析", "研究缺口台账", "创新性审计", "候选研究方向",
                   "可行性与风险", "推荐路线图", "证据附录"]

class LibError(RuntimeError):
    pass

def today() -> str:
    return time.strftime("%Y-%m-%d")

def norm_doi(doi: str) -> str:
    if not doi:
        return ""
    d = str(doi).strip().lower()
    for pre in ("https://doi.org/", "http://doi.org/", "doi.org/", "doi:"):
        if d.startswith(pre):
            d = d[len(pre):]
    return d.strip()

def norm_title(title: str) -> str:
    if not title:
        return ""
    t = unicodedata.normalize("NFKD", str(title))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", t.lower())

def token_overlap(a, b) -> float:
    """标题 token 重叠率（0-1），分母取较短方。"""
    ta = set(re.findall(r"[a-z0-9]+", str(a or "").lower()))
    tb = set(re.findall(r"[a-z0-9]+", str(b or "").lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))

class RateLimiter:
    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._last = 0.0

    def wait(self):
        now = time.time()
        if self._last and now - self._last < self.min_interval:
            time.sleep(self.min_interval - (now - self._last))
        self._last = time.time()

def _get_with_backoff(url, headers, retries, timeout, limiter, want_text):
    last = None
    for attempt in range(retries):
        if limiter:
            limiter.wait()
        req = urllib.request.Request(
            url, headers={"User-Agent": "project-due-diligence/0.1", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8")
                return body if want_text else json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                last = e
                time.sleep(min(2 ** attempt * 2, 30))
                continue
            raise LibError(f"HTTP {e.code} {url}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
            last = e
            time.sleep(min(2 ** attempt * 2, 30))
    raise LibError(f"fetch failed after {retries} tries: {url} ({last})")

def fetch_json(url, params=None, headers=None, retries=4, timeout=30, limiter=None):
    """GET 返回解析后的 JSON。429/5xx/网络错误指数退避重试。"""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    return _get_with_backoff(url, headers, retries, timeout, limiter, want_text=False)

def fetch_text(url, params=None, headers=None, retries=4, timeout=30, limiter=None):
    """GET 返回原始文本（用于 XML API）。退避策略同 fetch_json。"""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    return _get_with_backoff(url, headers, retries, timeout, limiter, want_text=True)

def save_json(path, data):
    ap = os.path.abspath(path)
    os.makedirs(os.path.dirname(ap) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(ap), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def raw_path(run_dir, source):
    os.makedirs(os.path.join(run_dir, "raw"), exist_ok=True)
    return os.path.join(run_dir, "raw", f"{source}_{time.strftime('%Y%m%dT%H%M%S')}_{os.getpid()}.json")

def append_search_log(run_dir, entry):
    p = os.path.join(run_dir, "search_log.json")
    log = load_json(p) or []
    entry = dict(entry)
    entry["id"] = f"S{len(log) + 1:03d}"
    entry.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
    log.append(entry)
    save_json(p, log)
    return entry["id"]

def load_records(run_dir):
    rawdir = os.path.join(run_dir, "raw")
    out = []
    if not os.path.isdir(rawdir):
        return out
    for fn in sorted(os.listdir(rawdir)):
        if fn.endswith(".json"):
            out.extend(load_json(os.path.join(rawdir, fn)) or [])
    return out

def default_entry(rec):
    access = "无法获取"
    if rec.get("oa_url"):
        access = "全文可读"
    elif rec.get("abstract"):
        access = "仅摘要"
    return {"paper_id": rec.get("paper_id", ""), "source": rec.get("source", ""),
            "source_id": rec.get("source_id", ""), "doi": rec.get("doi", ""),
            "title": rec.get("title", ""), "year": rec.get("year"),
            "authors": rec.get("authors", []), "venue": rec.get("venue", ""),
            "abstract": rec.get("abstract", ""), "citation_count": rec.get("citation_count", 0) or 0,
            "oa_url": rec.get("oa_url", ""), "paper_type": rec.get("paper_type", "other"),
            "n_sources": rec.get("n_sources", 1),
            "question_ids": [], "access_status": access, "reading_status": "待筛",
            "include_reason": "", "exclude_reason": "", "reading_level": "L1",
            "first_seen": today()}
