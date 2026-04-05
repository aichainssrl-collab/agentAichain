"""
Find and run test files for the given changed file.
Mapping strategy:
- agent_aichain/models/agent.py -> tests/unit/test_models.py
- agent_aichain/workers/agno_wrapper.py -> tests/unit/test_agno_wrapper.py
- agent_aichain/api/agents.py -> tests/unit/test_agents.py or tests/integration/test_*
- If no specific test found, run all tests/unit
"""
import subprocess
import sys
import pathlib

def find_tests(changed_file: str) -> list[str]:
    changed = pathlib.Path(changed_file)
    base = changed.name
    parent = changed.parent.name

    # Map parent package to test name
    test_dir = pathlib.Path("tests/unit")
    test_dir_int = pathlib.Path("tests/integration")

    candidates = []
    for td in [test_dir, test_dir_int]:
        if not td.exists():
            continue
        # test_<basename> (e.g. test_agno_wrapper.py)
        for f in td.glob(f"test_{base}"):
            candidates.append(str(f))
        # test_<parent>.py (e.g. models -> test_models.py)
        clean_parent = parent.split(".")[0] if "." in parent else parent
        for f in td.glob(f"test_{clean_parent}.py"):
            if str(f) not in candidates:
                candidates.append(str(f))

    return candidates

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(0)

    for fp in sys.argv[1:]:
        tests = find_tests(fp)
        if tests:
            subprocess.run(
                [sys.executable, "-m", "pytest"] + tests + ["-x", "-q", "--tb=short"],
                cwd="/Users/fred/dev/agentAichain"
            )
        else:
            subprocess.run(
                [sys.executable, "-m", "pytest", "tests/unit", "-x", "-q", "--tb=short"],
                cwd="/Users/fred/dev/agentAichain"
            )
