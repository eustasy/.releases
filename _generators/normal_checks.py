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
      travis = repo.get_contents('.travis.yml').content
      print(travis)
      travis = base64.b64decode(travis).decode("utf-8")
    
      if '143baa3fcdbd30302def591074cd44b09d42c4a4' in travis:
        self.normal_checks = '2.0'
      elif 'b92da74ddf4b05b698e2d12ebd56e965d6749397' in travis:
        self.normal_checks = '1.10.1'
      elif '2b23ee3dbb274409ae51a620ae9d6fef6516781a' in travis:
        self.normal_checks = '1.10.0'
      elif '649a7e0907c0ab4b342688e7d068b574a0945b3e' in travis:
        self.normal_checks = '1.9'
      elif '4256f55ef631900df06ca5c6167e21e6ed4cf55b' in travis:
        self.normal_checks = '1.7'
      elif 'd5f1a5d9e3fbac391b905f2bdfcdcdbfe465eabf' in travis:
        self.normal_checks = '1.4'
    
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
