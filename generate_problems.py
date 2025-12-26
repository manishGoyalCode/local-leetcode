import json
import os

CONFIG_FILE = "questions_config.json"
OUTPUT_DIR = "problems"


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def build_problem_json(problem):
    test_cases = []

    for t in problem["tests"]:
        if isinstance(t[0], list):
            test_cases.append({
                "input": ", ".join(map(repr, t[0])),
                "output": repr(t[1])
            })
        else:
            test_cases.append({
                "input": repr(t[0]),
                "output": repr(t[1])
            })

    return {
        "id": problem["id"],
        "title": problem["title"],
        "description": problem["description"],
        "difficulty": problem.get("difficulty", "Easy"),
        "tags": problem.get("tags", []),
        "hints": problem.get("hints", []),
        "function_signature": problem["signature"] + "\n    \"\"\"\n    Return result, do not print\n    \"\"\"\n    pass",
        "sample_input": test_cases[0]["input"],
        "sample_output": test_cases[0]["output"],
        "test_cases": test_cases
    }


def main():
    with open(CONFIG_FILE) as f:
        config = json.load(f)

    ensure_dir(OUTPUT_DIR)

    for day_key, day_data in config.items():
        day_dir = os.path.join(OUTPUT_DIR, day_key)
        ensure_dir(day_dir)

        for problem in day_data["problems"]:
            problem_json = build_problem_json(problem)
            file_path = os.path.join(day_dir, f"{problem['id']}.json")

            with open(file_path, "w") as f:
                json.dump(problem_json, f, indent=2)

            print(f"✅ Created {file_path}")


if __name__ == "__main__":
    main()
