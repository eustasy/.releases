import json
import yaml
import os
from github import Github
from operator import itemgetter

g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

ORG = 'eustasy'

DOC_FILES = {
  'security': 'SECURITY.md',
  'support': 'SUPPORT.md',
  'governance': 'GOVERNANCE.md',
}

DOC_FILE_LOCATIONS = ['', 'docs/', '.github/']


def get_repo_tree(repo):
  try:
    tree = repo.get_git_tree(repo.default_branch, recursive=True).tree
    return {item.path.lower() for item in tree}
  except Exception as e:
    print('Tree fetch failed for {}: {}'.format(repo.name, e))
    return set()


def has_doc_file(tree_paths, filename):
  filename_lower = filename.lower()
  for location in DOC_FILE_LOCATIONS:
    if (location + filename_lower) in tree_paths:
      return True
  return False


def has_funding(tree_paths):
  return '.github/funding.yml' in tree_paths or '.github/funding.yaml' in tree_paths


def has_discussion_templates(tree_paths):
  return any(p.startswith('.github/discussion_template/') for p in tree_paths)


def has_issue_template(tree_paths):
  if has_doc_file(tree_paths, 'ISSUE_TEMPLATE.md'):
    return True
  return any(p.startswith('.github/issue_template/') for p in tree_paths)


def has_pull_request_template(tree_paths):
  if has_doc_file(tree_paths, 'PULL_REQUEST_TEMPLATE.md'):
    return True
  return any(p.startswith('.github/pull_request_template/') for p in tree_paths)


class Repo:
  def __init__(self, repo, dot_github_tree):
    self.repo = repo
    self.pushed_at = repo.pushed_at
    self.updated_at = repo.updated_at

    self.code_of_conduct = 'missing'
    self.contributing = 'missing'
    self.issue_template = 'missing'
    self.pull_request_template = 'missing'
    self.readme = 'missing'
    self.security = 'missing'
    self.support = 'missing'
    self.governance = 'missing'
    self.funding = 'missing'
    self.discussion_templates = 'missing'

    try:
      headers, data = repo._requester.requestJsonAndCheck(
        "GET",
        repo.url + "/community/profile"
      )
      files = data.get('files') or {}
      self.code_of_conduct = self._profile_status(files.get('code_of_conduct'))
      self.contributing = self._profile_status(files.get('contributing'))
      self.issue_template = self._profile_status(files.get('issue_template'))
      self.pull_request_template = self._profile_status(files.get('pull_request_template'))
      self.readme = self._profile_status(files.get('readme'))
    except Exception as e:
      print('Community profile fetch failed for {}: {}'.format(repo.name, e))

    own_tree = get_repo_tree(repo)
    is_dot_github = (repo.name == '.github')

    for attr, filename in DOC_FILES.items():
      setattr(self, attr, self._tree_status(
        has_doc_file(own_tree, filename),
        has_doc_file(dot_github_tree, filename),
        is_dot_github,
      ))

    self.funding = self._tree_status(
      has_funding(own_tree),
      has_funding(dot_github_tree),
      is_dot_github,
    )
    self.discussion_templates = self._tree_status(
      has_discussion_templates(own_tree),
      has_discussion_templates(dot_github_tree),
      is_dot_github,
    )

    # /community/profile does not report org-level fallback for issue and
    # pull-request templates, so fill in those gaps from the tree.
    if self.issue_template != 'present':
      tree_status = self._tree_status(
        has_issue_template(own_tree),
        has_issue_template(dot_github_tree),
        is_dot_github,
      )
      if tree_status != 'missing':
        self.issue_template = tree_status
    if self.pull_request_template != 'present':
      tree_status = self._tree_status(
        has_pull_request_template(own_tree),
        has_pull_request_template(dot_github_tree),
        is_dot_github,
      )
      if tree_status != 'missing':
        self.pull_request_template = tree_status

  def _profile_status(self, entry):
    if not entry:
      return 'missing'
    url = entry.get('html_url') or entry.get('url') or ''
    if '/{}/'.format(self.repo.full_name) in url:
      return 'present'
    return 'fallback'

  def _tree_status(self, in_own, in_dot_github, is_dot_github_repo):
    if in_own:
      return 'present'
    if in_dot_github and not is_dot_github_repo:
      return 'fallback'
    return 'missing'


org = g.get_organization(ORG)

dot_github_tree = set()
try:
  dot_github_repo = org.get_repo('.github')
  dot_github_tree = get_repo_tree(dot_github_repo)
except Exception as e:
  print('Could not fetch .github org repo tree: {}'.format(e))

repos = []
for repo in org.get_repos():
  if repo.archived is False:
    print('Processing {}...'.format(repo.name))
    repos.append(Repo(repo, dot_github_tree))

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
    "readme": repo.readme,
    "security": repo.security,
    "support": repo.support,
    "governance": repo.governance,
    "funding": repo.funding,
    "discussion_templates": repo.discussion_templates,
  })

output = sorted(output, key=itemgetter('name'))

with open('_data/community_checks.yml', 'w') as file:
  print('Saving as YML')
  yaml.dump(output, file)

with open('_data/community_checks.json', 'w') as file:
  print('Saving as JSON')
  json.dump(output, file, indent=2)
