import json
import yaml
import os
import timeago
from datetime import datetime, timezone
from github import Github
from operator import itemgetter

g = Github(os.environ['GITHUB_TOKEN'], per_page=100)

ORG = 'eustasy'

now = datetime.now(timezone.utc)


def workflow_slug(path):
  # The Actions runs page lives at /actions/workflows/<slug>. For normal
  # workflows the slug is the file basename (security.yml); GitHub-managed
  # ones keep a subpath ("dynamic/pages/pages-build-deployment" ->
  # "pages/pages-build-deployment"), so strip only the known prefix.
  for prefix in ('.github/workflows/', 'dynamic/'):
    if path.startswith(prefix):
      return path[len(prefix):]
  return path.rsplit('/', 1)[-1]


def latest_run(workflow):
  # Runs come back newest-first; we only need the most recent one. totalCount
  # and [0] share the same first page fetch, so this is a single API call.
  try:
    runs = workflow.get_runs()
    if runs.totalCount:
      return runs[0]
  except Exception:
    pass
  return None


class Repo:
  def __init__(self, repo):
    self.name = repo.name
    self.default_branch = repo.default_branch
    self.workflows = []

    try:
      workflows = repo.get_workflows()
    except Exception as e:
      # Actions can be disabled at the repo or org level (403); treat as none.
      print('Workflow list failed for {}: {}'.format(repo.name, e))
      return

    for workflow in workflows:
      run = latest_run(workflow)
      self.workflows.append({
        'name': workflow.name,
        # Basename ("security.yml") for display; slug for the Actions runs URL.
        'file': workflow.path.rsplit('/', 1)[-1],
        'slug': workflow_slug(workflow.path),
        'state': workflow.state,
        'status': run.status if run else None,
        'conclusion': run.conclusion if run else None,
        'event': run.event if run else None,
        'branch': run.head_branch if run else None,
        'last_run': run.created_at.isoformat() if run else None,
        'timeago': timeago.format(run.created_at, now) if run else None,
        'run_url': run.html_url if run else workflow.html_url,
      })

    self.workflows.sort(key=itemgetter('name', 'file'))


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
    'workflows': repo.workflows,
  })

output = sorted(output, key=itemgetter('name'))

with open('_data/workflows.yml', 'w', encoding='utf-8') as file:
  print('Saving as YML')
  yaml.dump(output, file, allow_unicode=True)

with open('_data/workflows.json', 'w', encoding='utf-8') as file:
  print('Saving as JSON')
  json.dump(output, file, indent=2, ensure_ascii=False)
