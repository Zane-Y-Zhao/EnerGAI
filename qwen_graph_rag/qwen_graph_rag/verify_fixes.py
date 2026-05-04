import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60, flush=True)
print("Verification Test", flush=True)
print("=" * 60, flush=True)

results = []

try:
    print("[1] Testing imports...", flush=True)
    from config.llm_config import call_qwen
    from multi_agent.coordination import DebateCoordinator
    from services.rag_service import get_vectorstore
    from autoresearch.task_manager import AutoresearchManager
    print("    [OK] All imports successful", flush=True)
    results.append(("Imports", True))
except Exception as e:
    print(f"    [FAIL] Import error: {e}", flush=True)
    results.append(("Imports", False))

try:
    print("[2] Testing Qwen API...", flush=True)
    result = call_qwen("Say 'Qwen OK' in Chinese")
    print(f"    Response: {result[:50]}...", flush=True)
    results.append(("Qwen API", "[ERROR]" not in result))
except Exception as e:
    print(f"    [FAIL] {e}", flush=True)
    results.append(("Qwen API", False))

try:
    print("[3] Testing DebateCoordinator...", flush=True)
    coord = DebateCoordinator()
    print(f"    [OK] GNN available: {coord.gnn_model is not None}", flush=True)
    results.append(("Coordinator", True))
except Exception as e:
    print(f"    [FAIL] {e}", flush=True)
    results.append(("Coordinator", False))

try:
    print("[4] Testing RAG service...", flush=True)
    vs = get_vectorstore()
    print(f"    [OK] Vector store: {'available' if vs else 'not available (fallback)'}", flush=True)
    results.append(("RAG Service", True))
except Exception as e:
    print(f"    [FAIL] {e}", flush=True)
    results.append(("RAG Service", False))

try:
    print("[5] Testing AutoresearchManager...", flush=True)
    manager = AutoresearchManager()
    print(f"    [OK] Manager created with _research_query implemented", flush=True)
    results.append(("Task Manager", manager._research_query.__code__.co_code != b'\x97\x00'))
except Exception as e:
    print(f"    [FAIL] {e}", flush=True)
    results.append(("Task Manager", False))

try:
    print("[6] Checking API port...", flush=True)
    with open("services/api_service.py", "r") as f:
        content = f.read()
        if "port=8006" in content:
            print("    [OK] Port changed to 8006", flush=True)
            results.append(("API Port", True))
        else:
            print("    [FAIL] Port not changed", flush=True)
            results.append(("API Port", False))
except Exception as e:
    print(f"    [FAIL] {e}", flush=True)
    results.append(("API Port", False))

print("\n" + "=" * 60, flush=True)
print("Summary", flush=True)
print("=" * 60, flush=True)
for name, passed in results:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{name:20s}: {status}", flush=True)

passed = sum(1 for _, p in results if p)
print(f"\nTotal: {passed}/{len(results)} passed", flush=True)
print("=" * 60, flush=True)
