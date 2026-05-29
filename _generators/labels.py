import json
import yaml
import os
from github import Github
from operator import itemgetter

g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

ORG = 'eustasy'


def normalise_color(color):
  return (color or '').strip().lstrip('#').lower()


def normalise_description(description):
  return (description or '').strip()


# Load the hand-maintained org default labels (the source of truth, since
# GitHub does not expose org default labels via the API).
with open('_data/default_labels.yml') as file:
  defaults = yaml.safe_load(file) or []

default_labels = {}
for label in defaults:
  default_labels[label['name']] = {
    'color': normalise_color(label.get('color')),
    'description': normalise_description(label.get('description')),
  }


class Repo:
  def __init__(self, repo):
    self.name = repo.name
    self.default_branch = repo.default_branch
    self.present = []
    self.missing = []
    self.mismatched = []
    self.extra = []

    repo_labels = {}
    try:
      for label in repo.get_labels():
        repo_labels[label.name] = {
          'color': normalise_color(label.color),
          'description': normalise_description(label.description),
        }
    except Exception as e:
      print('Label fetch failed for {}: {}'.format(repo.name, e))

    for name, default in default_labels.items():
      if name not in repo_labels:
        self.missing.append(name)
        continue
      current = repo_labels[name]
      diffs = []
      if current['color'] != default['color']:
        diffs.append('color')
      if current['description'] != default['description']:
        diffs.append('description')
      if diffs:
        self.mismatched.append({'name': name, 'diff': ', '.join(diffs)})
      else:
        self.present.append(name)

    for name in repo_labels:
      if name not in default_labels:
        self.extra.append(name)

    self.missing.sort()
    self.mismatched.sort(key=itemgetter('name'))
    self.present.sort()
    self.extra.sort()


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
    'default_branch': repo.default_branch,
    'present': repo.present,
    'missing': repo.missing,
    'mismatched': repo.mismatched,
    'extra': repo.extra,
  })

output = sorted(output, key=itemgetter('name'))

with open('_data/labels.yml', 'w') as file:
  print('Saving as YML')
  yaml.dump(output, file)

with open('_data/labels.json', 'w') as file:
  print('Saving as JSON')
  json.dump(output, file, indent=2)
