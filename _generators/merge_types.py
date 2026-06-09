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

class MergeSettingsUnreadable(Exception):
  pass

# GitHub only returns these fields to a token with admin access on the repo.
# For any other repo they come back as None -- which is NOT the same as
# "disabled". Coercing None to False (as this script used to) silently
# publishes wrong data, so we treat None as a hard failure instead.
MERGE_FIELDS = (
  'allow_rebase_merge',
  'allow_squash_merge',
  'allow_merge_commit',
  'allow_auto_merge',
  'delete_branch_on_merge',
)

class Repo:
  def __init__(self, repo):
    self.name = repo.name
    self.default_branch = repo.default_branch
    for field in MERGE_FIELDS:
      value = getattr(repo, field)
      if value is None:
        raise MergeSettingsUnreadable(
          '{}.{} came back as None -- the token lacks admin access to read '
          'merge settings for this repo. Aborting so good data is not '
          'overwritten with incorrect values.'.format(repo.name, field)
        )
      setattr(self, field, bool(value))

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
    "default_branch": repo.default_branch,
    "allow_rebase_merge": repo.allow_rebase_merge,
    "allow_squash_merge": repo.allow_squash_merge,
    "allow_merge_commit": repo.allow_merge_commit,
    "allow_auto_merge": repo.allow_auto_merge,
    "delete_branch_on_merge": repo.delete_branch_on_merge
  })

output = sorted(output, key=itemgetter('name')) 

with open('_data/merge_types.yml', 'w') as file:
    print ('Saving as YML')
    yaml.dump(output, file)
  
with open('_data/merge_types.json', 'w') as file:
    print ('Saving as JSON')
    json.dump(output, file, indent=2, ensure_ascii=False)
