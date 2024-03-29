import os
import json
import yaml
from github import Github

g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

org = g.get_organization('eustasy')

repos = []
for repo in org.get_repos():
  # Skip archived repositories
  if repo.archived is False:
    #print (repo)
    print ('Processing {}...'.format(repo.name))
    repos.append(repo.name)

#repos = sorted(repos, key=lambda repo: repo.name, reverse=False)

with open('_data/list_repositories.yml', 'w') as file:
    print ('Saving as YML')
    yaml.dump(repos, file)
  
with open('_data/list_repositories.json', 'w') as file:
    print ('Saving as JSON')
    json.dump(repos, file, indent=2)
