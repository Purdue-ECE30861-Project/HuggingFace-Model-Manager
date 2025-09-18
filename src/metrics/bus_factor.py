from metric import BaseMetric  # pyright: ignore[reportMissingTypeStubs]
import requests
from dotenv import load_dotenv
import os, re

github_pattern = re.compile(r"^(https:\/\/)?github.com\/([^\/]+)\/([^\/]+)\/?(.*)$")

# Bus factor metric
# Assumes that the url for this metric points to a github codebase
class BusFactorMetric(BaseMetric):
    metric_name: str = "bus_factor"
    response: requests.Response
    graphql_query = """
{
repository(name:"{name}", owner:"{owner}"){
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

    def calculate_score(self) -> float:
        """
        Abstract method to calculate the metric score.
        Should be implemented by subclasses.
        Returns:
            float: The calculated score.
        """
        ...

    def setup_resources(self):
        load_dotenv()

        # parse out name and owner
        matches = github_pattern.match(self.url)
        if matches is None:
            raise ValueError("invalid GitHub URL")
        
        owner = matches.group(2)
        name = matches.group(3)

        if type(owner) is not str or type(name) is not str:
            raise ValueError("invalid GitHub URL")

        url = "https://api.github.com/graphql"
        json = {"query": self.graphql_query.format(owner = owner, name = name)}
        headers = {"Authorization": f"bearer {os.getenv("GRAPHQL_TOKEN")}"}
        self.response = requests.post(url=url, json=json, headers=headers)
        return super().setup_resources()
