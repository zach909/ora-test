import math
import unittest

from social_power import compute_power, report


class PowerTotalsTest(unittest.TestCase):
    def test_power_sums_to_one_and_is_non_negative(self):
        people = ["Ana", "Ben", "Cy", "Dee"]
        opinions = {
            "Ana": {"Ben": 0.9, "Cy": -0.4},
            "Ben": {"Ana": 0.5, "Dee": 1.0},
            "Cy": {"Ana": 1.0},
            "Dee": {"Cy": 0.2, "Ben": -1.0},
        }
        power = compute_power(people, opinions)

        self.assertAlmostEqual(sum(power.values()), 1.0, places=9)
        for person in people:
            self.assertGreaterEqual(power[person], 0.0)

    def test_empty_group_has_no_power(self):
        self.assertEqual(compute_power([], {}), {})

    def test_single_person_has_all_the_power(self):
        self.assertEqual(compute_power(["Solo"], {}), {"Solo": 1.0})

    def test_no_opinions_gives_everyone_equal_power(self):
        people = ["Ana", "Ben", "Cy"]
        power = compute_power(people, {})

        for person in people:
            self.assertAlmostEqual(power[person], 1 / 3, places=9)


class PowerRulesTest(unittest.TestCase):
    def test_mutual_positive_regard_in_pairs_gives_equal_power(self):
        people = ["Ana", "Ben", "Cy", "Dee"]
        opinions = {
            "Ana": {"Ben": 1.0},
            "Ben": {"Ana": 1.0},
            "Cy": {"Dee": 1.0},
            "Dee": {"Cy": 1.0},
        }
        power = compute_power(people, opinions)

        for person in people:
            self.assertAlmostEqual(power[person], 0.25, places=6)

    def test_most_esteemed_person_has_the_most_power(self):
        people = ["Ana", "Ben", "Cy", "Dee"]
        opinions = {
            "Ben": {"Ana": 1.0},
            "Cy": {"Ana": 1.0},
            "Dee": {"Ana": 1.0},
            "Ana": {"Ben": 0.5},
        }
        power = compute_power(people, opinions)

        self.assertEqual(max(people, key=lambda p: power[p]), "Ana")

    def test_person_nobody_views_positively_has_the_least_power(self):
        people = ["Ana", "Ben", "Cy", "Dee"]
        opinions = {
            "Ana": {"Ben": 1.0, "Cy": 1.0},
            "Ben": {"Ana": 1.0, "Cy": 1.0},
            "Cy": {"Ana": 1.0, "Ben": 1.0},
            "Dee": {"Ana": 1.0},
        }
        power = compute_power(people, opinions)

        self.assertEqual(min(people, key=lambda p: power[p]), "Dee")

    def test_regard_from_a_high_power_person_counts_for_more(self):
        # Hub is liked by two fans, so Hub has high power. Lowly is liked by nobody.
        # X is liked by Hub; Y is liked by Lowly. X should end up with more power than Y.
        people = ["Hub", "X", "Y", "Lowly", "Fan1", "Fan2"]
        opinions = {
            "Fan1": {"Hub": 1.0},
            "Fan2": {"Hub": 1.0},
            "Hub": {"X": 1.0},
            "Lowly": {"Y": 1.0},
        }
        power = compute_power(people, opinions)

        self.assertGreater(power["Hub"], power["Lowly"])
        self.assertGreater(power["X"], power["Y"])

    def test_negative_opinions_do_not_change_power(self):
        people = ["Ana", "Ben", "Cy"]
        base = {
            "Ben": {"Ana": 0.8},
            "Cy": {"Ana": 0.6, "Ben": 0.2},
        }
        with_negative = {
            "Ben": {"Ana": 0.8},
            "Cy": {"Ana": 0.6, "Ben": 0.2},
            "Ana": {"Cy": -1.0},
        }
        before = compute_power(people, base)
        after = compute_power(people, with_negative)

        for person in people:
            self.assertAlmostEqual(before[person], after[person], places=9)

    def test_opinion_strength_scales_influence(self):
        # Ben and Cy both view a person with a positive opinion. Ben's view is stronger.
        people = ["Ana", "Ben", "Cy", "Dee"]
        opinions = {
            "Ben": {"Ana": 1.0},
            "Cy": {"Dee": 0.2},
        }
        power = compute_power(people, opinions)

        self.assertGreater(power["Ana"], power["Dee"])

    def test_result_is_deterministic(self):
        people = ["Ana", "Ben", "Cy"]
        opinions = {"Ana": {"Ben": 0.3}, "Ben": {"Cy": 0.7}, "Cy": {"Ana": 0.9}}

        self.assertEqual(compute_power(people, opinions), compute_power(people, opinions))


class ValidationTest(unittest.TestCase):
    def test_self_opinion_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_power(["Ana", "Ben"], {"Ana": {"Ana": 1.0}})

    def test_opinion_above_one_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_power(["Ana", "Ben"], {"Ana": {"Ben": 1.5}})

    def test_opinion_below_minus_one_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_power(["Ana", "Ben"], {"Ana": {"Ben": -1.01}})

    def test_nan_opinion_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_power(["Ana", "Ben"], {"Ana": {"Ben": math.nan}})

    def test_unknown_observer_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_power(["Ana", "Ben"], {"Zed": {"Ben": 0.5}})

    def test_unknown_target_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_power(["Ana", "Ben"], {"Ana": {"Zed": 0.5}})

    def test_duplicate_names_are_rejected(self):
        with self.assertRaises(ValueError):
            compute_power(["Ana", "Ana"], {})


class ReportTest(unittest.TestCase):
    def test_report_lists_everyone_with_power_and_views(self):
        people = ["Ana", "Ben", "Cy"]
        opinions = {
            "Ben": {"Ana": 0.8},
            "Cy": {"Ana": 0.6, "Ben": -0.2},
        }
        lines = report(people, opinions).splitlines()

        self.assertEqual(len(lines), 3)
        # Ana is viewed positively by both others, so she is listed first with the most power.
        self.assertTrue(lines[0].startswith("Ana: power "))
        self.assertTrue(lines[0].endswith("thinks of others: no opinions given"))
        self.assertTrue(any(line.startswith("Ben: power ") and line.endswith("Ana +0.80") for line in lines))
        self.assertTrue(any(line.startswith("Cy: power ") and line.endswith("Ana +0.60, Ben -0.20") for line in lines))


if __name__ == "__main__":
    unittest.main()
