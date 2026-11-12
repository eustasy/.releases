import json
import yaml
import os
import urllib.request
from github import Auth, Github
from operator import itemgetter

token = os.environ['GITHUB_TOKEN']
g = Github(auth=Auth.Token(token), per_page=100)

class MergeSettingsUnreadable(Exception):
  pass

# The REST repository object only carries allow_*_merge for admins. GraphQL
# exposes the same settings to anyone who can read the repository, so a
# read-only token is enough.
MERGE_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    rebaseMergeAllowed
    squashMergeAllowed
    mergeCommitAllowed
    autoMergeAllowed
    deleteBranchOnMerge
  }
}
"""

MERGE_FIELDS = {
  'allow_rebase_merge': 'rebaseMergeAllowed',
  'allow_squash_merge': 'squashMergeAllowed',
  'allow_merge_commit': 'mergeCommitAllowed',
  'allow_auto_merge': 'autoMergeAllowed',
  'delete_branch_on_merge': 'deleteBranchOnMerge',
}


def merge_settings(owner, name):
  body = json.dumps({'query': MERGE_QUERY, 'variables': {'owner': owner, 'name': name}}).encode('utf-8')
  request = urllib.request.Request(
    'https://api.github.com/graphql',
    data=body,
    headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
  )
  with urllib.request.urlopen(request) as response:  # noqa: S310 -- fixed https URL
    payload = json.load(response)
  repository = (payload.get('data') or {}).get('repository')
  if payload.get('errors') or repository is None:
    raise MergeSettingsUnreadable(
      '{}/{}: merge settings unreadable: {}. Aborting so good data is not '
      'overwritten with incorrect values.'.format(owner, name, payload.get('errors'))
    )
  return repository


class Repo:
  def __init__(self, repo):
    self.name = repo.name
    self.default_branch = repo.default_branch
    settings = merge_settings(repo.owner.login, repo.name)
    for field, graphql_field in MERGE_FIELDS.items():
      value = settings.get(graphql_field)
      if value is None:
        raise MergeSettingsUnreadable(
          '{}.{} came back as None. Aborting so good data is not overwritten '
          'with incorrect values.'.format(repo.name, field)
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
