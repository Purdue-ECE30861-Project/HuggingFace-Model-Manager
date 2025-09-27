from metric import BaseMetric  # pyright: ignore[reportMissingTypeStubs]
import requests
from dotenv import load_dotenv
import os, re, json
import heapq

github_pattern = re.compile(r"^(.*)?github.com\/([^\/]+)\/([^\/]+)\/?(.*)$")


# Bus factor metric
# Assumes that the url for this metric points to a github codebase
class BusFactorMetric(BaseMetric):
    metric_name: str = "bus_factor"
    codebase_url: str = ""
    response: requests.Response
    # get most recent 30 commits on (most) branches since 2020
    graphql_query = """
{
repository(name:"%s", owner:"%s"){
    refs(refPrefix:"refs/heads/", first:30){
      edges{
        node{
          target{
        ...on Commit{
          history(first:30, since:"2020-01-01T00:00:00.000Z") {
            edges {
              node {
                author{
                  email
                }
              }
            }
          }
        }
      }
        }
      }
    }
  }
  }"""

    def __init__(self):
        super().__init__()

    # separated into functions for testing

    # parse the given response
    # Returns: total number of commits and dictionary of authors and commit counts
    def parse_response(self) -> tuple[int, dict[str, int]]:
        # create dictionary of commit counts
        response_obj = json.loads(self.response.text)
        try:
            response_obj["data"]["repository"]["refs"]["edges"]
        except TypeError:
            raise ValueError("Repository is not public or does not exist")
        commit_score: dict[str, int] = {}
        total_commits = 0
        for branch in response_obj["data"]["repository"]["refs"]["edges"]:
            for commit in branch["node"]["target"]["history"]["edges"]:
                author = commit["node"]["author"]["email"]
                commit_score[author] = commit_score.get(author, 0) + 1
                total_commits += 1

        return total_commits, commit_score

    def calculate_bus_factor(
        self, total_commits: int, commit_score: dict[str, int]
    ) -> float:
        if total_commits < 1:
            return 0.0
        pqueue = [
            (total_commits - commits, commits)
            for _, commits in list(commit_score.items())
        ]
        heapq.heapify(pqueue)
        num_contributors = len(pqueue)

        # start taking away authors
        bus_numerator = 0
        remaining_commits = total_commits
        while remaining_commits / total_commits > 0.5:
            bussed_author_commits = heapq.heappop(pqueue)[1]
            remaining_commits -= bussed_author_commits
            bus_numerator += 1
        if bus_numerator <= 1:
            return 0.0
        bus_factor = 2 * bus_numerator / num_contributors
        return bus_factor if bus_factor < 1.0 else 1.0

    def calculate_score(self) -> float:
        total_commits, commit_score = self.parse_response()
        return self.calculate_bus_factor(total_commits, commit_score)

    def setup_resources(self):
        load_dotenv()

        # parse out name and owner
        matches = github_pattern.match(self.codebase_url)
        if matches is None:
            raise ValueError("invalid GitHub URL")

        owner = matches.group(2)
        name = matches.group(3)

        # this should theoretically never run but will cause errors to be
        # raised if the regex parsing is faulty
        if type(owner) is not str or type(name) is not str:
            raise ValueError("invalid GitHub URL")  # pragma: no cover

        url = "https://api.github.com/graphql"
        json = {"query": self.graphql_query % (name, owner)}
        headers = {"Authorization": f"bearer {os.getenv("GRAPHQL_TOKEN")}"}
        self.response = requests.post(url=url, json=json, headers=headers)
        return super().setup_resources()
