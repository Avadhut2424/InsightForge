import time
import requests
import json
import sys

API_BASE = "http://localhost:8000"

EVAL_TOPICS = [
    # In-domain topics (8)
    {"category": "in_domain", "topic": "the environmental impact of AI computing hardware and energy consumption"},
    {"category": "in_domain", "topic": "economic transformation and labor market disruption from artificial intelligence"},
    {"category": "in_domain", "topic": "geopolitical competition and national sovereignty in artificial intelligence"},
    {"category": "in_domain", "topic": "the energy consumption and water requirements of artificial intelligence data centers"},
    {"category": "in_domain", "topic": "workforce displacement and productivity effects of artificial intelligence automation"},
    {"category": "in_domain", "topic": "geopolitical governance and technological sovereignty challenges in artificial intelligence"},
    {"category": "in_domain", "topic": "carbon emissions and environmental sustainability of artificial intelligence infrastructure"},
    {"category": "in_domain", "topic": "economic productivity and structural labor reallocation driven by artificial intelligence"},
    
    # Out-of-domain topics (4)
    {"category": "out_of_domain", "topic": "history of ancient Egyptian pyramid construction and architecture"},
    {"category": "out_of_domain", "topic": "traditional fermentation methods and culinary history of French cheeses"},
    {"category": "out_of_domain", "topic": "deep sea bioluminescence mechanisms in cephalopods and marine invertebrates"},
    {"category": "out_of_domain", "topic": "quantum electrodynamics and Feynman diagram calculations in particle physics"},
    
    # Borderline topics (3)
    {"category": "borderline", "topic": "artificial intelligence energy consumption compared to traditional data processing methods"},
    {"category": "borderline", "topic": "economic impact of artificial intelligence on wage inequality and union collective bargaining"},
    {"category": "borderline", "topic": "national artificial intelligence sovereignty initiatives in developing countries"}
]

def run_batch():
    results = []
    print(f"=== Starting Evaluation Batch: {len(EVAL_TOPICS)} fresh runs via {API_BASE}/research ===", flush=True)
    
    for i, item in enumerate(EVAL_TOPICS, start=1):
        category = item["category"]
        topic = item["topic"]
        print(f"\n[{i}/{len(EVAL_TOPICS)}] Submitting ({category}): '{topic}'", flush=True)
        
        t0 = time.time()
        try:
            resp = requests.post(f"{API_BASE}/research", json={"topic": topic}, timeout=30)
            if resp.status_code != 202:
                print(f"  FAILED to submit: HTTP {resp.status_code} - {resp.text}", flush=True)
                results.append({"category": category, "topic": topic, "run_id": None, "status": "submission_failed", "duration": 0})
                continue
            
            data = resp.json()
            run_id = data["run_id"]
            print(f"  Accepted: run_id={run_id}. Polling status...", flush=True)
        except Exception as e:
            print(f"  Error submitting request: {e}", flush=True)
            results.append({"category": category, "topic": topic, "run_id": None, "status": "error", "duration": 0})
            continue

        # Poll until complete
        poll_interval = 5
        final_status = "unknown"
        summary_info = {}
        
        while True:
            time.sleep(poll_interval)
            elapsed = time.time() - t0
            try:
                poll_resp = requests.get(f"{API_BASE}/research/{run_id}", timeout=30)
                if poll_resp.status_code == 200:
                    run_data = poll_resp.json()
                    status = run_data.get("status")
                    if status != "running":
                        final_status = status
                        summary_info = run_data.get("summary", {})
                        print(f"  Completed run_id={run_id} in {elapsed:.1f}s with status='{final_status}'", flush=True)
                        if summary_info:
                            print(f"    Summary: {summary_info}", flush=True)
                        break
                    else:
                        steps = run_data.get("summary", {}).get("steps_completed", 0)
                        revs = run_data.get("summary", {}).get("revision_count", 0)
                        print(f"    [+{elapsed:.0f}s] status=running, steps={steps}, revs={revs}", flush=True)
                elif poll_resp.status_code == 500:
                    final_status = "failed"
                    print(f"  Run {run_id} failed with 500 internal error: {poll_resp.text}", flush=True)
                    break
                else:
                    print(f"  Unexpected poll response HTTP {poll_resp.status_code}: {poll_resp.text}", flush=True)
            except Exception as e:
                print(f"  Error during polling: {e}", flush=True)
                
            if elapsed > 600:  # 10 min safety timeout
                print(f"  TIMEOUT polling run_id={run_id} after {elapsed:.1f}s", flush=True)
                final_status = "timeout"
                break
                
        results.append({
            "category": category,
            "topic": topic,
            "run_id": run_id,
            "status": final_status,
            "duration": round(time.time() - t0, 2),
            "summary": summary_info
        })
        
    print("\n=== Evaluation Batch Finished ===", flush=True)
    with open("eval_runs_output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Saved run summaries to eval_runs_output.json", flush=True)

if __name__ == "__main__":
    run_batch()
