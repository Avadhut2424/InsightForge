"""
Phase 10 Automated Test 1: Retrieval Quality against a Known In-Domain Query.
Formalizes Phase 3's verify_search.py as a deterministic quality assertion.
"""

import pytest
from app.mcp_servers.db_lookup import similarity_search

DISTANCE_THRESHOLD = 0.255

def test_retrieval_quality_known_query():
    """
    Asserts that a fixed in-domain query returns chunks whose min distance
    is below the 0.255 calibrated threshold, and the top result originates
    from an expected known source document in the knowledge base.
    """
    query = "What are the latest advancements in solar power technology?"
    res = similarity_search(query=query, top_k=5)
    
    assert res.get("success") is True, f"Search failed: {res.get('error')}"
    results = res.get("data", {}).get("results", [])
    assert len(results) >= 3, f"Expected at least 3 chunks, got {len(results)}"
    
    # Assert distance threshold
    min_dist = results[0]["distance"]
    assert min_dist <= DISTANCE_THRESHOLD, (
        f"Top chunk distance {min_dist:.4f} exceeds threshold {DISTANCE_THRESHOLD}"
    )
    
    # Assert expected source and document
    top_chunk = results[0]
    assert top_chunk["source"] in ["Wikipedia", "ArXiv", "RSS"], (
        f"Unexpected source: {top_chunk['source']}"
    )
    assert "Solar" in top_chunk["title"] or "Renewable" in top_chunk["title"], (
        f"Expected Solar or Renewable document, got '{top_chunk['title']}'"
    )
    print(f"\n[PASS] Known query retrieval verified: min_distance={min_dist:.4f} <= {DISTANCE_THRESHOLD}, source='{top_chunk['source']}', title='{top_chunk['title']}'")

if __name__ == "__main__":
    test_retrieval_quality_known_query()
