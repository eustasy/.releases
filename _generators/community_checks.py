import json
import yaml
import os
from github import Github
from operator import itemgetter

g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

ORG = 'eustasy'

class Repo:
  def __init__(self, repo):
    self.repo = repo
    self.pushed_at = repo.pushed_at
    self.updated_at = repo.updated_at

    self.code_of_conduct = 'missing'
    self.contributing = 'missing'
    self.issue_template = 'missing'
    self.pull_request_template = 'missing'
    self.readme = 'missing'

    try:
      headers, data = repo._requester.requestJsonAndCheck(
        "GET",
        repo.url + "/community/profile"
      )
      files = data.get('files') or {}
      self.code_of_conduct = self._status(files.get('code_of_conduct'))
      self.contributing = self._status(files.get('contributing'))
      self.issue_template = self._status(files.get('issue_template'))
      self.pull_request_template = self._status(files.get('pull_request_template'))
      self.readme = self._status(files.get('readme'))
    except Exception as e:
      print('Community profile fetch failed for {}: {}'.format(repo.name, e))

  def _status(self, entry):
    if not entry:
      return 'missing'
    url = entry.get('html_url') or entry.get('url') or ''
    if '/{}/'.format(self.repo.full_name) in url:
      return 'present'
    return 'fallback'

org = g.get_organization(ORG)

repos = []
for repo in org.get_repos():
  if repo.archived is False:
    print('Processing {}...'.format(repo.name))
    repos.append(Repo(repo))

output = []
for repo in repos:
  output.append({
    "name": repo.repo.name,
    "pushed_at": repo.pushed_at.isoformat(),
    "updated_at": repo.updated_at.isoformat(),
    "code_of_conduct": repo.code_of_conduct,
    "contributing": repo.contributing,
    "issue_template": repo.issue_template,
    "pull_request_template": repo.pull_request_template,
    "readme": repo.readme
  })

output = sorted(output, key=itemgetter('name'))

with open('_data/community_checks.yml', 'w') as file:
  print('Saving as YML')
  yaml.dump(output, file)

with open('_data/community_checks.json', 'w') as file:
  print('Saving as JSON')
  json.dump(output, file, indent=2)
