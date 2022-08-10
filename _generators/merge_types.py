import datetime
import timeago
import json
import yaml
import os
import sys
from github import Github
from operator import itemgetter
from github.GithubException import UnknownObjectException as GithubUnknownObjectException

now = datetime.datetime.now()
g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

class NoReleasesFound(Exception):
  pass

class Repo:
  def __init__(self, repo):
    self.name = repo.name
    self.allow_rebase_merge = repo.allow_rebase_merge
    self.allow_squash_merge = repo.allow_squash_merge
    self.allow_merge_commit = repo.allow_merge_commit

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
    "name": repo.name,
    "allow_rebase_merge": repo.allow_rebase_merge,
    "allow_squash_merge": repo.allow_squash_merge,
    "allow_merge_commit": repo.allow_merge_commit
  })

output = sorted(output, key=itemgetter('name')) 

with open('_data/merge_types.yml', 'w') as file:
    print ('Saving as YML')
    yaml.dump(output, file)
  
with open('_data/merge_types.json', 'w') as file:
    print ('Saving as JSON')
    json.dump(output, file, indent=2)
