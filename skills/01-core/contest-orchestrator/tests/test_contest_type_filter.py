#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 8 contest type filter tests.

Covers retrieve signature extension with contest_filter and bounded
ranking weight within same relevance bucket.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from memory.retrieval import retrieve, _contest_match_weight, _contest_filter_stats  # noqa: E402


class ContestFilterSignatureTests(unittest.TestCase):
    def test_retrieve_accepts_contest_filter_none(self):
        """retrieve with contest_filter=None preserves default behavior."""
        fp = {'primary': '优化决策', 'keywords': ['线性规划'], 'data_scale': 'medium'}
        prior = retrieve(fp, top=5, contest_filter=None)
        self.assertIn('experience_coverage', prior)
        self.assertIn('retrieval_status', prior)

    def test_retrieve_accepts_contest_filter_cm_b(self):
        """retrieve with contest_filter='CM-B' runs without error."""
        fp = {'primary': '优化决策', 'keywords': ['线性规划'], 'data_scale': 'medium'}
        prior = retrieve(fp, top=5, contest_filter='CM-B')
        self.assertIn('experience_coverage', prior)
        coverage = prior['experience_coverage']
        self.assertIn('contest_filter', coverage)

    def test_contest_filter_stats_returns_matched_count(self):
        """_contest_filter_stats returns matched and unknown counts."""
        entries = [
            {'id': 'FD-001', 'contest_type': 'CM-B', 'source': '2023高教社杯B题'},
            {'id': 'FD-002', 'contest_type': 'CM-A', 'source': '2023高教社杯A题'},
            {'id': 'FD-003', 'source': '通用经验'},
        ]
        stats = _contest_filter_stats(entries, 'CM-B')
        self.assertEqual(stats['contest_filter'], ['CM-B'])
        self.assertEqual(stats['matched_contest_count'], 1)
        self.assertEqual(stats['unknown_contest_count'], 1)


class ContestMatchWeightTests(unittest.TestCase):
    def test_matched_entry_gets_boost(self):
        """Entries matching contest_filter get weight 1.10."""
        entry = {'contest_type': 'CM-B', 'source': '2023B题'}
        weight = _contest_match_weight(entry, 'CM-B')
        self.assertEqual(weight, 1.10)

    def test_unmatched_entry_gets_penalty(self):
        """Entries not matching contest_filter get weight 0.95."""
        entry = {'contest_type': 'CM-A', 'source': '2023A题'}
        weight = _contest_match_weight(entry, 'CM-B')
        self.assertEqual(weight, 0.95)

    def test_unknown_entry_gets_neutral(self):
        """Entries with unknown contest_type get neutral weight 1.0."""
        entry = {'source': '通用经验'}
        weight = _contest_match_weight(entry, 'CM-B')
        self.assertEqual(weight, 1.0)

    def test_no_filter_gets_neutral(self):
        """Without contest_filter, all entries get neutral weight 1.0."""
        entry = {'contest_type': 'CM-B', 'source': '2023B题'}
        weight = _contest_match_weight(entry, None)
        self.assertEqual(weight, 1.0)

    def test_wildcard_filter_matches_prefix(self):
        """CM-* wildcard filter matches any CM- contest type."""
        entry = {'contest_type': 'CM-B', 'source': '2023B题'}
        weight = _contest_match_weight(entry, 'CM-*')
        self.assertEqual(weight, 1.10)


if __name__ == "__main__":
    unittest.main()
