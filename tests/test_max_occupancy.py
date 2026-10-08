"""Unit tests for max_occupancy, derived from ANALYSIS.md.

Covers the provided examples (happy path) and the edge-cases table.
Cases tied to the pending `peak_end` decision (longest window) are not covered yet.
"""

import unittest

from main import max_occupancy


class TestProvidedExamples(unittest.TestCase):
    def test_overlapping_bookings(self):
        self.assertEqual(max_occupancy([(9, 12), (10, 13), (11, 14)]), (3, 11, 12))

    def test_touching_bookings_do_not_overlap(self):
        self.assertEqual(max_occupancy([(9, 10), (10, 11), (11, 12)]), (1, 9, 10))

    def test_empty_input(self):
        self.assertEqual(max_occupancy([]), (0, None, None))


class TestEdgeCases(unittest.TestCase):
    def assert_result_and_logs(self, bookings, expected, expected_logs):
        with self.assertLogs() as logs:
            self.assertEqual(max_occupancy(bookings), expected)
        self.assertEqual(len(logs.records), expected_logs)

    def test_several_separate_peaks_of_equal_size(self):
        self.assertEqual(max_occupancy([(0, 2), (1, 3), (10, 12), (11, 13)]), (2, 1, 2))

    def test_nested_booking(self):
        self.assertEqual(max_occupancy([(0, 10), (2, 3)]), (2, 2, 3))

    def test_negative_values(self):
        self.assert_result_and_logs([(9, 12), (-3, 2)], (1, 9, 12), 1)

    def test_zero_duration_booking(self):
        self.assert_result_and_logs([(0, 10), (5, 5)], (1, 0, 10), 1)

    def test_inverted_booking(self):
        self.assert_result_and_logs([(9, 12), (14, 9)], (1, 9, 12), 1)

    def test_malformed_entries(self):
        self.assert_result_and_logs(
            [(9, 12), None, (1, 2, 3), (9.5, 12), (True, 5)], (1, 9, 12), 4
        )

    def test_every_entry_invalid(self):
        self.assert_result_and_logs([(5, 5), (14, 9)], (0, None, None), 2)


if __name__ == "__main__":
    unittest.main()
