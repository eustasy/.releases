import base64
import json
import yaml
import os
import sys
from github import Github
from operator import itemgetter

g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

class Repo:
  def __init__(self, repo):
    self.repo = repo
    self.normal_checks = False

    try:
      normal = repo.get_contents('.github/workflows/normal.yml').content
      print(normal)
      normal = base64.b64decode(normal).decode("utf-8")
      if 'af240a6c8960177bcb1d07815732df7eb15970c1' in normal:
        self.normal_checks = '3.0.1'
      elif '5408f4ab384ceebf276686578963498f1ade3f55' in normal:
        self.normal_checks = '3.0'
    except:
      pass

    print (self.normal_checks)

org = g.get_organization('eustasy')

repos = []
for repo in org.get_repos():
  # Skip archived repositories
  if repo.archived is False:
    print ('Processing {}...'.format(repo.name))
    repos.append(Repo(repo))

#repos = sorted(repos, key=lambda repo: repo.name, reverse=False)

output = []
for repo in repos:
  output.append ({
    "name": repo.repo.name,
    "normal_checks": repo.normal_checks
  })

output = sorted(output, key=itemgetter('name')) 

with open('_data/normal_checks.yml', 'w') as file:
    print ('Saving as YML')
    yaml.dump(output, file)
  
with open('_data/normal_checks.json', 'w') as file:
    print ('Saving as JSON')
    json.dump(output, file, indent=2)
