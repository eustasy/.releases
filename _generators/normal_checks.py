import base64
import json
import yaml
import os
from github import Github
from operator import itemgetter

g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

ORG = 'eustasy'

# The .Normal config repo. Its published release tags are the version strings
# stamped into the header of each installed workflow: the first line of
# .github/workflows/security.yml reads e.g. "# eustasy/.Normal 4.0beta8".
# The newest release is the current "tagged release"; older tags are behind.
NORMAL_REPO = 'eustasy/.normal'


def normal_release_tags():
  # Newest-first by publish date, including pre-releases (the 4.0betas are all
  # pre-releases, so get_latest_release() — which skips them — is deliberately
  # not used). Sort on published_at, not created_at: created_at is the target
  # commit's date, which is not the order the betas were released in.
  repo = g.get_repo(NORMAL_REPO)
  releases = [r for r in repo.get_releases() if not r.draft]
  releases.sort(key=lambda r: r.published_at or r.created_at, reverse=True)
  return [release.tag_name for release in releases]


class Repo:
  def __init__(self, repo, tags, latest):
    self.repo = repo
    self.default_branch = repo.default_branch
    self.normal_checks = False
    self.status = False

    # New convention (.Normal 4.0+): the version is stamped into the header of
    # security.yml. Match the header against the published release tags. endswith
    # keeps "4.0beta1" from matching a "4.0beta10" header.
    try:
      security = repo.get_contents('.github/workflows/security.yml').content
      security = base64.b64decode(security).decode('utf-8')
      header = security.splitlines()[0].strip()
      if 'eustasy/.Normal' in header:
        for tag in tags:
          if header.endswith(tag):
            self.normal_checks = tag
            self.status = 'current' if tag == latest else 'behind'
            break
    except Exception:
      pass

    # Old convention (.Normal 3.x and earlier): a single, unstamped normal.yml
    # workflow. Every old install collapses to "3.x" and is marked outdated.
    if self.normal_checks is False:
      try:
        repo.get_contents('.github/workflows/normal.yml')
        self.normal_checks = '3.x'
        self.status = 'outdated'
      except Exception:
        pass


org = g.get_organization(ORG)

tags = normal_release_tags()
latest = tags[0] if tags else None
print('Latest .Normal release: {}'.format(latest))

repos = []
for repo in org.get_repos():
  # Skip archived repositories
  if repo.archived is False:
    print('Processing {}...'.format(repo.name))
    repos.append(Repo(repo, tags, latest))

output = []
for repo in repos:
  output.append({
    'name': repo.repo.name,
    'default_branch': repo.default_branch,
    'normal_checks': repo.normal_checks,
    'status': repo.status,
  })

output = sorted(output, key=itemgetter('name'))

with open('_data/normal_checks.yml', 'w', encoding='utf-8') as file:
  print('Saving as YML')
  yaml.dump(output, file, allow_unicode=True)

with open('_data/normal_checks.json', 'w', encoding='utf-8') as file:
  print('Saving as JSON')
  json.dump(output, file, indent=2, ensure_ascii=False)
