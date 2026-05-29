import base64
import json
import yaml
import os
from github import Github
from operator import itemgetter

g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

ORG = 'eustasy'

# Dependabot config lives at one of these paths.
CONFIG_PATHS = ['.github/dependabot.yml', '.github/dependabot.yaml']

# Lockfile-based ecosystems where `dependency-type: "all"` also covers indirect
# (transitive) dependencies. For ecosystems without a lockfile / transitive
# concept (github-actions, docker, ...) `all` is equivalent to `direct`, so
# `direct` is not a shortfall there.
INDIRECT_ALL_ECOSYSTEMS = {
  'bundler',
  'pip',
  'composer',
  'cargo',
  'gomod',
  'uv',
  'npm',
  'bun',
  'pnpm',
  'yarn',
  'nuget',
}


def load_config(repo):
  for path in CONFIG_PATHS:
    try:
      raw = repo.get_contents(path).content
      text = base64.b64decode(raw).decode('utf-8')
      return yaml.safe_load(text)
    except Exception:
      continue
  return None


def directory_label(update):
  # Newer configs use a `directories` list; older ones a single `directory`.
  if 'directories' in update and update['directories']:
    return ', '.join(str(d) for d in update['directories'])
  return str(update.get('directory', '/'))


def allows_all(update):
  allow = update.get('allow') or []
  for rule in allow:
    if isinstance(rule, dict) and rule.get('dependency-type') == 'all':
      return True
  return False


class Repo:
  def __init__(self, repo):
    self.name = repo.name
    self.has_config = False
    self.updates = []

    config = load_config(repo)
    if config is None:
      return

    self.has_config = True
    for update in config.get('updates') or []:
      if not isinstance(update, dict):
        continue
      schedule = update.get('schedule') or {}
      ecosystem = update.get('package-ecosystem', 'unknown')
      # `target-branch` is optional; without it Dependabot uses the default branch.
      target_branch = update.get('target-branch') or repo.default_branch
      self.updates.append({
        'package_ecosystem': ecosystem,
        'target_branch': target_branch,
        'directory': directory_label(update),
        'interval': schedule.get('interval', 'unknown'),
        'all_dependencies': allows_all(update),
        'supports_all': ecosystem in INDIRECT_ALL_ECOSYSTEMS,
      })

    self.updates.sort(key=itemgetter('package_ecosystem', 'target_branch', 'directory'))


org = g.get_organization(ORG)

repos = []
for repo in org.get_repos():
  # Skip archived repositories
  if repo.archived is False:
    print('Processing {}...'.format(repo.name))
    repos.append(Repo(repo))

output = []
for repo in repos:
  output.append({
    'name': repo.name,
    'has_config': repo.has_config,
    'updates': repo.updates,
  })

output = sorted(output, key=itemgetter('name'))

with open('_data/dependabot.yml', 'w', encoding='utf-8') as file:
  print('Saving as YML')
  yaml.dump(output, file, allow_unicode=True)

with open('_data/dependabot.json', 'w', encoding='utf-8') as file:
  print('Saving as JSON')
  json.dump(output, file, indent=2, ensure_ascii=False)
