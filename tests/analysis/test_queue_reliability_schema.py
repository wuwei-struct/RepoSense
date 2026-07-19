import json
import os
import unittest
from functools import lru_cache

from reposense.analysis.ai.pattern_export import export_patterns
from reposense.analysis.messaging.reliability_schema import (
    COVERAGE_STATUSES,
    MATCH_STATUSES,
    RETRY_STATUSES,
    normalize_correlation,
)
from reposense.scan import run_scan
from tests._tmpdir import make_temp_dir


def fixture_repo():
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "fixtures",
            "repos",
            "queue_retry_idempotency_min",
        )
    )


@lru_cache(maxsize=1)
def build_queue_reliability_run():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_dir = run_scan(
        fixture_repo(),
        make_temp_dir(prefix="queue_reliability_"),
        os.path.join(root, "rulesets", "demo_v1"),
        os.path.join(root, "presets", "demo.json"),
    )
    export_patterns(run_dir)
    return run_dir


def load_artifact(name):
    with open(
        os.path.join(build_queue_reliability_run(), name),
        "r",
        encoding="utf-8",
    ) as handle:
        return json.load(handle)


def correlations():
    return load_artifact("queue_reliability_correlations.json")[
        "correlations"
    ]


def correlation(framework, channel):
    return next(
        item
        for item in correlations()
        if item["framework"] == framework
        and item["queue_or_topic"] == channel
    )


class QueueReliabilitySchemaTest(unittest.TestCase):
    def test_stable_id_and_allowed_statuses(self):
        raw = {
            "framework": "bullmq",
            "channel_kind": "queue",
            "queue_or_topic": "jobs",
            "match_status": "matched",
            "retry_status": "explicit_retry",
            "coverage_status": "retry_without_consumer_guard",
        }
        first = normalize_correlation(raw)
        second = normalize_correlation(raw)
        self.assertEqual(first["correlation_id"], second["correlation_id"])
        self.assertIn(first["match_status"], MATCH_STATUSES)
        self.assertIn(first["retry_status"], RETRY_STATUSES)
        self.assertIn(first["coverage_status"], COVERAGE_STATUSES)


if __name__ == "__main__":
    unittest.main()
