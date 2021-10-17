import base64
import json
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

#repos = sorted(repos, key=lambda repo: repo.name, reverse=False)

json_out = []
for repo in repos:
  json_out.append ({
    "name": repo.repo.name,
    "license_file": repo.license_file,
    "license_year": repo.license_year
  })
  
with open('_data/license_year.json', 'w') as outfile:
    json.dump(json_out, outfile, indent=2)
