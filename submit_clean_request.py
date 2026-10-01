import urllib.request
import json
import time

def main():
    print("=== Submitting Research Request to Clean-Restart System ===", flush=True)
    payload = {"topic": "the environmental impact of AI computing hardware and energy consumption"}
    req = urllib.request.Request(
        "http://localhost:8000/research",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    t0 = time.time()
    resp = urllib.request.urlopen(req)
    res = json.loads(resp.read().decode("utf-8"))
    print(f"HTTP Response ({resp.status}): {res}", flush=True)
    
    run_id = res["run_id"]
    print(f"Polling /research/{run_id} until completion...", flush=True)
    
    while True:
        time.sleep(5)
        elapsed = time.time() - t0
        try:
            poll_resp = urllib.request.urlopen(f"http://localhost:8000/research/{run_id}")
            data = json.loads(poll_resp.read().decode("utf-8"))
            status = data.get("status")
            if status != "running":
                print(f"\n[COMPLETED] Run {run_id} finished in {elapsed:.1f}s with status='{status}'", flush=True)
                print(f"Summary: {data.get('summary')}", flush=True)
                sections = data.get("sections", {})
                print(f"Total sections generated: {len(sections)}", flush=True)
                for idx, (sq, sec) in enumerate(sections.items(), 1):
                    print(f"  Section {idx}: '{sq}' -> status='{sec.get('status')}', revisions={sec.get('revision_count')}", flush=True)
                    print(f"    Assembled text: {sec.get('assembled_text', '')[:120]}...", flush=True)
                break
            else:
                steps = data.get("summary", {}).get("steps_completed", 0)
                revs = data.get("summary", {}).get("revision_count", 0)
                print(f"  [+{elapsed:.0f}s] status=running, steps_completed={steps}, revisions={revs}", flush=True)
        except Exception as e:
            print(f"  Error polling: {e}", flush=True)

if __name__ == "__main__":
    main()
