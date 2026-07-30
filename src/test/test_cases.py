# -*- coding: utf-8 -*-
"""
run_cases.py — chay test_cases.json

    python3 run_cases.py                       # chay tren bot.py tham chieu
    BOT_IMPL=my_module.answer python3 run_cases.py
    python3 run_cases.py --priority P0         # chi chay case chan phat hanh
    python3 run_cases.py --group phan_tang_nguon

Ket qua ghi nguoc vao test_cases.json o truong status va actual.
"""
import argparse, json, re, time
from pathlib import Path
from bot import load_impl

HERE = Path(__file__).parent
answer = load_impl()
D = json.load(open(HERE / "discord_qa_mock.json", encoding="utf-8"))
THREADS = {t["thread_id"]: t for t in D["threads"]}
LINK = re.compile(r"^https://discord\.com/channels/\d+/\d+/(\d+)$")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(?<!\d)(0\d{9}|\+84\d{9})(?!\d)")
LEAK = ["system prompt", "you are a", "bạn là trợ lý", "###"]


def check(exp, r, inp, ms):
    """Tra ve list loi. Rong = PASS."""
    e, res = [], r.get("results", [])
    ids = [i["thread_id"] for i in res]

    if "has_answer" in exp and r.get("has_answer") != exp["has_answer"]:
        e.append(f"has_answer={r.get('has_answer')} (mong doi {exp['has_answer']})")
    if "reason" in exp and r.get("reason") != exp["reason"]:
        e.append(f"reason={r.get('reason')!r} (mong doi {exp['reason']!r})")
    if "max_results" in exp and len(res) > exp["max_results"]:
        e.append(f"tra ve {len(res)} ket qua (toi da {exp['max_results']})")
    if "min_results" in exp and len(res) < exp["min_results"]:
        e.append(f"tra ve {len(res)} ket qua (toi thieu {exp['min_results']})")
    if "results_contains_any" in exp and not (set(ids) & set(exp["results_contains_any"])):
        e.append(f"khong co thread mong doi trong top-{len(res)}; nhan duoc {ids}")
    if "results_excludes" in exp and (set(ids) & set(exp["results_excludes"])):
        e.append("tra ve thread bi cam")
    if exp.get("verified_first"):
        f = [i["verified"] for i in res]
        if f != sorted(f, reverse=True):
            e.append(f"nguon chua xac minh xep tren nguon da xac minh: {f}")
    if exp.get("all_thread_ids_exist"):
        bad = [i for i in ids if i not in THREADS]
        if bad:
            e.append(f"bia thread_id: {bad}")
    if exp.get("verified_flag_matches_corpus"):
        for i in res:
            if i["thread_id"] in THREADS and i["verified"] != THREADS[i["thread_id"]]["verified_answer"]:
                e.append(f"co verified sai o {i['thread_id']}")
    if exp.get("title_verbatim"):
        for i in res:
            if i["thread_id"] in THREADS and i["title"] != THREADS[i["thread_id"]]["title"]:
                e.append(f"title bi viet lai o {i['thread_id']}")
    if exp.get("snippet_verbatim"):
        for i in res:
            t = THREADS.get(i["thread_id"])
            if not t:
                continue
            body = " ||| ".join([t["question"]["content"]] + [x["content"] for x in t["replies"]])
            if not i["snippet"].rstrip(". ") or i["snippet"].rstrip(". ") not in body:
                e.append(f"snippet khong co trong thread {i['thread_id']} - dau hieu bia noi dung")
    if exp.get("link_matches_thread"):
        for i in res:
            m = LINK.match(i.get("link", ""))
            t = THREADS.get(i["thread_id"])
            if not m or not t:
                e.append(f"link sai dinh dang o {i['thread_id']}")
            elif m.group(1) not in {t["thread_id"], *(x["message_id"] for x in t["replies"])}:
                e.append(f"link tro ra ngoai thread {i['thread_id']}")
    if "answered_by_role_in" in exp:
        for i in res:
            if i["verified"] and i.get("answered_by_role") not in exp["answered_by_role_in"]:
                e.append(f"verified nhung role={i.get('answered_by_role')!r}")
    if exp.get("clarifying_question_present") and not r.get("clarifying_question"):
        e.append("thieu cau hoi lai")
    if "tag_labcoach" in exp and r.get("tag_labcoach") != exp["tag_labcoach"]:
        e.append(f"tag_labcoach={r.get('tag_labcoach')} (mong doi {exp['tag_labcoach']})")

    blob = json.dumps(r, ensure_ascii=False)
    if exp.get("no_prompt_leak") and any(x in blob.lower() for x in LEAK):
        e.append("lo dau hieu prompt he thong")
    if exp.get("no_pii") and (EMAIL.search(blob) or PHONE.search(blob)):
        e.append("lo thong tin ca nhan")
    if exp.get("stable_across_runs"):
        if [i["thread_id"] for i in answer(inp).get("results", [])] != ids:
            e.append("hai lan goi ra hai ket qua khac nhau")
    if "max_latency_ms" in exp and ms > exp["max_latency_ms"]:
        e.append(f"do tre {ms:.0f}ms (toi da {exp['max_latency_ms']}ms)")
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--priority")
    ap.add_argument("--group")
    ap.add_argument("--verbose", "-v", action="store_true")
    a = ap.parse_args()

    path = HERE / "test_cases.json"
    doc = json.load(open(path, encoding="utf-8"))
    cases = doc["cases"]
    sel = [c for c in cases
           if (not a.priority or c["priority"] == a.priority)
           and (not a.group or c["group"] == a.group)]

    stats, fails = {}, []
    for c in sel:
        t0 = time.perf_counter()
        try:
            r = answer(c["input"])
            crashed = None
        except Exception as ex:
            r, crashed = {}, f"{type(ex).__name__}: {ex}"
        ms = (time.perf_counter() - t0) * 1000

        errs = [f"CRASH {crashed}"] if crashed else check(c["expect"], r, c["input"], ms)
        if crashed and c["expect"].get("no_crash") is not True:
            pass
        c["status"] = "pass" if not errs else "fail"
        c["actual"] = {"latency_ms": round(ms, 1), "errors": errs,
                       "n_results": len(r.get("results", []))}
        g = stats.setdefault(c["group"], [0, 0])
        g[0] += 1
        g[1] += (c["status"] == "pass")
        if errs:
            fails.append(c)

    json.dump(doc, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"\n{'NHOM':26s} PASS")
    for g, (n, p) in sorted(stats.items()):
        mark = "OK " if p == n else "!! "
        print(f"{mark}{g:24s} {p}/{n}")
    total = sum(n for n, _ in stats.values())
    passed = sum(p for _, p in stats.values())
    print(f"\nTONG: {passed}/{total}")
    for prio in ["P0", "P1", "P2"]:
        sub = [c for c in sel if c["priority"] == prio]
        if sub:
            ok = sum(1 for c in sub if c["status"] == "pass")
            print(f"  {prio}: {ok}/{len(sub)}" + ("  <- CHAN DEMO" if prio == "P0" and ok < len(sub) else ""))

    if a.verbose and fails:
        print("\n--- CHI TIET CASE DO ---")
        for c in fails:
            print(f"\n{c['case_id']} [{c['priority']}] {c['group']} (owner {c['owner']})")
            print(f"  input : {c['input']!r}")
            for e in c["actual"]["errors"]:
                print(f"  loi   : {e}")


if __name__ == "__main__":
    main()
