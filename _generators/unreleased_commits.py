import timeago
import json
import yaml
import os
import sys
from datetime import datetime, timezone
from github import Github
from operator import itemgetter
from github.GithubException import GithubException
from github.GithubException import UnknownObjectException as GithubUnknownObjectException

now = datetime.now(timezone.utc)
g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

class NoReleasesFound(Exception):
  pass

def release_dict(release):
  return {
    "version": release.tag_name,
    "release_date": release.created_at.isoformat(),
    "timeago": timeago.format(release.created_at, now),
    "title": release.title,
    "body": release.body,
    "href": release.html_url
  }

class Repo:
  def __init__(self, repo):
    self.repo = repo
    self.default_branch = repo.default_branch

    # Newest release first, which is the order GitHub returns them in.
    self.releases = list(self.repo.get_releases())
    if len(self.releases) == 0:
      raise NoReleasesFound

    self.last_release_timestamp = self.releases[0].created_at.timestamp()

    # Surface the default branch plus any branch a release was actually cut from
    # (e.g. a maintenance branch like Phoenix's `3.x`). target_commitish can name
    # a branch that no longer exists (an old `master`), so keep only live branches.
    branch_names = {branch.name for branch in self.repo.get_branches()}
    release_branches = sorted(
      name for name in {release.target_commitish for release in self.releases}
      if name in branch_names and name != self.default_branch
    )

    # The default branch is always first so it anchors the de-duplication below.
    self.branches = []
    for name in [self.default_branch] + release_branches:
      line = self.release_line(name)
      if line is not None:
        self.branches.append(line)

    # Drop a non-default branch that just tracks the same release as the default
    # branch; it isn't a distinct release line worth listing on its own.
    if self.branches:
      default_version = self.branches[0]["release"]["version"]
      self.branches = [self.branches[0]] + [
        line for line in self.branches[1:]
        if line["release"]["version"] != default_version
      ]

    # Show the freshest release line first.
    self.branches = sorted(
      self.branches, key=lambda line: line["release"]["release_date"], reverse=True
    )

  def release_line(self, branch_name):
    # The latest release reachable from this branch (behind_by == 0 means the
    # branch contains the release tag), with an accurate per-branch commits-since
    # count from the compare graph (ahead_by) rather than a date-filter guess.
    fallback = None
    for release in self.releases:
      try:
        comparison = self.repo.compare(release.tag_name, branch_name)
      except GithubException:
        continue
      if fallback is None:
        fallback = (release, comparison)
      if comparison.behind_by == 0:
        return self.build_line(branch_name, release, comparison.ahead_by)

    # No release is an ancestor of this branch; fall back to the newest release so
    # the branch still appears, counting how far the branch has moved past it.
    if fallback is not None:
      release, comparison = fallback
      return self.build_line(branch_name, release, comparison.ahead_by)
    return None

  def build_line(self, branch_name, release, new_commits):
    return {
      "name": branch_name,
      "is_default": branch_name == self.default_branch,
      "new_commits": new_commits,
      "release": release_dict(release)
    }

org = g.get_organization('eustasy')

repos = []
no_releases = []
for repo in org.get_repos():
  # Skip archived repositories
  if repo.archived is False:
    print ('Processing {}...'.format(repo.name))
    try:
      repos.append(Repo(repo))
    # This catches repos that don't have releases and records them separately
    except NoReleasesFound:
      no_releases.append({
        "name": repo.name,
        "default_branch": repo.default_branch
      })

output = []
for repo in repos:
  output.append ({
    "name": repo.repo.name,
    "default_branch": repo.default_branch,
    "branches": repo.branches,
    "releases": [release_dict(release) for release in repo.releases]
  })

output = sorted(output, key=itemgetter('name'))

no_releases = sorted(no_releases, key=itemgetter('name'))

with open('_data/unreleased_commits.yml', 'w') as file:
    print ('Saving as YML')
    yaml.dump(output, file)

with open('_data/unreleased_commits.json', 'w') as file:
    print ('Saving as JSON')
    json.dump(output, file, indent=2, ensure_ascii=False)

with open('_data/no_releases.yml', 'w') as file:
    print ('Saving No Releases as YML')
    yaml.dump(no_releases, file)

with open('_data/no_releases.json', 'w') as file:
    print ('Saving No Releases as JSON')
    json.dump(no_releases, file, indent=2, ensure_ascii=False)
