import subprocess
import tempfile
import sys
import logging

logger = logging.getLogger(__name__)


def evaluate_code(user_code, problem):
    logger.info(f"Runner started for problem: {problem.get('id', 'unknown')}")
    results = []

    for idx, case in enumerate(problem["test_cases"], start=1):

        full_code = (
            user_code.strip()
            + "\n\n"
            + "if __name__ == '__main__':\n"
            + f"    result = solve({case['input']})\n"
            + "    if result is not None:\n"
            + "        print(result)\n"
        )

        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False
        ) as f:
            f.write(full_code)
            filename = f.name

        try:
            proc = subprocess.run(
                [sys.executable, filename],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if proc.stderr:
                results.append({
                    "index": idx,
                    "status": "error",
                    "error": proc.stderr.strip()
                })
                logger.warning(f"Result: ERROR (Stderr) - {proc.stderr.strip()[:100]}...")
                break
                
        except subprocess.TimeoutExpired:
            logger.warning("Result: TIMEOUT (2s)")
            results.append({
                "index": idx,
                "status": "error",
                "error": "Time Limit Exceeded (2s)"
            })
            break
        except Exception as e:
            results.append({
                "index": idx,
                "status": "error",
                "error": f"Internal Execution Error: {str(e)}"
            })
            break
        finally:
            # Clean up the temp file
            import os
            try:
                os.unlink(filename)
            except OSError:
                pass

        output = proc.stdout.strip()
        expected = case["output"]

        if output == expected:
            results.append({
                "index": idx,
                "status": "passed"
            })
        else:
            results.append({
                "index": idx,
                "status": "failed",    
                "input": case["input"],
                "expected": expected,
                "got": output
            })
            break

    passed_all = all(r["status"] == "passed" for r in results)
    
    if passed_all:
        logger.info("Result: PASSED ALL TESTS")
    else:
        logger.info(f"Result: FAILED (Passed {sum(1 for r in results if r['status']=='passed')}/{len(problem['test_cases'])})")

    return passed_all, results
