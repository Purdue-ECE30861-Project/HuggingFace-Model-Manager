import unittest
from metrics.bus_factor import *  # pyright: ignore[reportWildcardImportFromLibrary]


class TestBustFactor(unittest.TestCase):
    metric_instance: BusFactorMetric

    def setUp(self):
        self.metric_instance = BusFactorMetric()

    # calculation testing

    def testLopsidedTeam(self):
        team = {"hard_carry": 35, "normal_dev": 10, "lazy_user": 1}
        total_commits = sum(team.values())
        self.assertAlmostEqual(
            self.metric_instance.calculate_bus_factor(total_commits, team), 0.0
        )

    def testEqualTeam(self):
        team = {"cool_dev": 20, "great_dev": 20, "some_guy": 20}
        total_commits = sum(team.values())
        self.assertAlmostEqual(
            self.metric_instance.calculate_bus_factor(total_commits, team), 1.0
        )

    def testSoloDev(self):
        team = {"one_guy_from_nebraska": 172}
        total_commits = sum(team.values())
        self.assertAlmostEqual(
            self.metric_instance.calculate_bus_factor(total_commits, team), 0.0
        )

    def testEmptyRepo(self):
        team: dict[str, int] = {}
        total_commits = 0
        self.assertAlmostEqual(
            self.metric_instance.calculate_bus_factor(total_commits, team), 0.0
        )

    def testAverageTeam(self):
        team: dict[str, int] = {
            "lead_programmer": 20,
            "team_member": 10,
            "team_member_2": 10,
            "tryhard": 15,
            "future_successor": 20,
            "intern": 3,
        }
        total_commits = sum(team.values())
        # total commits is 78, 78/2 = 39
        #  remove lead programmer and future successor, remove half the commits.
        self.assertAlmostEqual(
            self.metric_instance.calculate_bus_factor(total_commits, team),
            2 * 2 / len(team),
        )

    # test repo parsing
    def test_team_repo(self):
        # archived project, unlikely to change much
        self.metric_instance.set_url("https://github.com/silica-dev/TerrorCTF")
        commit_score = {
            "silicasandwhich@github.com": 18,
            "marinom@rose-hulman.edu": 6,
            "rogerscm@rose-hulman.edu": 5,
            "102613108+CarsonRogers@users.noreply.github.com": 1,
        }
        total_commits = 30
        self.metric_instance.setup_resources()
        parsed_response = self.metric_instance.parse_response()
        self.assertDictEqual(parsed_response[1], commit_score)
        self.assertEqual(parsed_response[0], total_commits)

    def test_solo_repo(self):
        # you can't remove commits from a repository
        self.metric_instance.set_url(
            "https://www.github.com/silica-dev/2nd_to_ft_conversion_script"
        )
        total_commits = 25
        self.metric_instance.setup_resources()
        parsed_response = self.metric_instance.parse_response()
        self.assertGreaterEqual(total_commits, parsed_response[0])
        self.assertGreaterEqual(
            total_commits,
            parsed_response[1]["43558271+Silicasandwhich@users.noreply.github.com"],
        )

    def test_nonexistent_repo(self):
        self.metric_instance.set_url(
            "https://github.com/silica-dev/PLEASEDONTACTUALLYMAKETHIS"
        )
        self.metric_instance.setup_resources()
        with self.assertRaises(ValueError):
            self.metric_instance.parse_response()

    # url parsing
    def test_invalid_url(self):
        self.metric_instance.set_url("sdvx.org")
        with self.assertRaises(ValueError):
            self.metric_instance.run()

    def test_no_http(self):
        self.metric_instance.set_url("github.com/silica-dev/TerrorCTF")
        self.metric_instance.setup_resources()
        self.assertTrue(self.metric_instance.response.ok)

    def test_specific_branch(self):
        self.metric_instance.set_url(
            "https://github.com/leftwm/leftwm/tree/flake_update"
        )
        self.metric_instance.setup_resources()
        self.assertTrue(self.metric_instance.response.ok)

    # full integration

    # test repo parsing
    def test_team_repo_full(self):
        # archived project, unlikely to change much
        self.metric_instance.set_url("https://github.com/silica-dev/TerrorCTF")
        # commit_score = {
        #    "silicasandwhich@github.com": 18,
        #    "marinom@rose-hulman.edu": 6,
        #    "rogerscm@rose-hulman.edu": 5,
        #    "102613108+CarsonRogers@users.noreply.github.com": 1,
        # }
        # remove silicasandwhich@github.com and more than 50% is gone
        self.metric_instance.run()
        self.assertAlmostEqual(self.metric_instance.score, 0.0)
