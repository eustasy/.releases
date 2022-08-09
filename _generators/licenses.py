import base64
import json
import yaml
import os
import sys
import re
from github import Github
from operator import itemgetter

g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

class Repo:
  def __init__(self, repo):
    self.repo = repo
    self.license_file = False
    self.license_type = False
    self.license_year = False

    try:
      self.license_file = repo.get_license().path
      print(self.license_file)
      license = repo.get_contents(self.license_file).content
      license = base64.b64decode(license).decode("utf-8")
      #print(license)
      
      if 'MIT License' in license:
        self.license_type = 'MIT'
      elif 'Apache License' and 'Version 2.0, January 2004' in license:
        self.license_type = 'Apache 2.0'
      elif 'GNU AFFERO GENERAL PUBLIC LICENSE' and 'Version 3, 29 June 2007' in license:
        self.license_type = 'AGPLv3'
      elif 'GNU Lesser General Public License v3.0' and 'Version 3, 29 June 2007' in license:
        self.license_type = 'LGPLv3'
      elif 'GNU GENERAL PUBLIC LICENSE' and 'Version 3, 29 June 2007' in license:
        self.license_type = 'GPLv3'
      elif 'Mozilla Public License Version 2.0' in license:
        self.license_type = 'Mozilla 2.0'
        
      print(self.license_type)

      license = re.findall('(?:(?:19|20)[0-9]{2})', license)
      print(license)
      license.sort()
      print(license)
      self.license_year = license[-1]
      print(self.license_year)
    
    except:
      pass

org = g.get_organization('eustasy')

repos = []
for repo in org.get_repos():
  # Skip archived repositories
  if repo.archived is False:
    print ('Processing {}...'.format(repo.name))
    repos.append(Repo(repo))

output = []
for repo in repos:
  output.append ({
    "name": repo.repo.name,
    "license_file": repo.license_file,
    "license_type": repo.license_type,
    "license_year": repo.license_year
  })

output = sorted(output, key=itemgetter('name')) 

with open('_data/licenses.yml', 'w') as file:
    print ('Saving as YML')
    yaml.dump(output, file)
  
with open('_data/licenses.json', 'w') as file:
    print ('Saving as JSON')
    json.dump(output, file, indent=2)
