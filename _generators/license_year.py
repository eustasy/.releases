import base64
import json
import yaml
import os
import sys
import re
from github import Github

g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

class Repo:
  def __init__(self, repo):
    self.repo = repo
    self.license_file = False
    self.license_year = False

    try:
      self.license_file = repo.get_license().path
      print(self.license_file)
      license = repo.get_contents(self.license_file).content
      license = base64.b64decode(license).decode("utf-8")
      #print(license)
      license = re.findall('(?:(?:19|20)[0-9]{2})', license)
      print(license)
      self.license_year = license[-1]
      print (self.license_year)
    
    except:
      pass

org = g.get_organization('eustasy')

repos = []
for repo in org.get_repos():
  # Skip archived repositories
  if repo.archived is False:
    print ('Processing {}...'.format(repo.name))
    repos.append(Repo(repo))

json_out = []
for repo in repos:
  json_out.append ({
    "name": repo.repo.name,
    "license_file": repo.license_file,
    "license_year": repo.license_year
  })

json_out.sort()

with open('_data/license_year.yml', 'w') as file:
    print ('Saving as YML')
    yaml.dump(repos, file)
  
with open('_data/license_year.json', 'w') as file:
    print ('Saving as JSON')
    json.dump(repos, file, indent=2)
