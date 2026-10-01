"""
Unified Automated Test Suite Runner for InsightForge AI.
Runs all core tests across Phases 6-8 plus Phase 10 retrieval quality and end-to-end smoke tests.
Tracks and reports exact execution duration.
"""

import sys
import time
import subprocess

TEST_FILES = [
    "app/agents/tests/test_routing.py",
    "app/agents/tests/test_retrieval_quality.py",
    "app/agents/tests/test_phase6.py",
    "app/agents/tests/test_retriever_ood.py",
    "app/agents/tests/test_revision_cap.py",
    "app/agents/tests/test_forced_revision.py",
    "app/agents/tests/test_critic_suite.py",
    "app/agents/tests/test_end_to_end_smoke.py"
]

def main():
    print("=" * 70)
    print("        RUNNING CONSOLIDATED INSIGHTFORGE TEST SUITE")
    print("=" * 70)
    print(f"Target test files ({len(TEST_FILES)} total):")
    for tf in TEST_FILES:
        print(f"  - {tf}")
    print("-" * 70)
    
    cmd = [sys.executable, "-m", "pytest", "-v"] + TEST_FILES
    print(f"Executing: {' '.join(cmd)}\n", flush=True)
    
    t0 = time.time()
    result = subprocess.run(cmd)
    duration = time.time() - t0
    
    print("\n" + "=" * 70)
    print(f"TEST SUITE FINISHED in {duration:.2f} seconds ({duration/60:.2f} minutes)")
    print(f"Exit Code: {result.returncode}")
    print("=" * 70)
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
