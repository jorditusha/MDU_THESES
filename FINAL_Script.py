import calendar
import csv
import datetime
import time

from github import Github, GithubIntegration
from langdetect import detect


def get_access_token():
    # Replace with your GitHub App's ID
    APP_ID = "12345"
    # Replace with the installation ID for your GitHub App
    INSTALLATION_ID = "1235467"
    # Replace with the path to your GitHub App's private key file
    PRIVATE_KEY_FILE = "<key>.pem"
    with open(PRIVATE_KEY_FILE, "r") as f:
        PRIVATE_KEY = f.read()
    integration = GithubIntegration(APP_ID, PRIVATE_KEY)
    return integration.get_access_token(INSTALLATION_ID).token


g = Github(login_or_token=get_access_token())

query = "filename:.drawio"

# Search for .drawio files
codes = g.search_code(query=query, sort='indexed', order='desc')

data = []
headers = ['Name', 'URL', 'Description', 'Stars', 'Forks', 'DiagramCommits', 'FileNameContents', 'RepoTotalCommits',
           'ContributorsCount', 'Diagram_contributors', 'Watchers', 'Issues', 'Releases', 'Pulls', 'FilePath',
           'fileChangesCommits', 'fileChangesComments', 'CommitDates', 'DateCreated', 'repo_total_commits']

# Initialize a set to store processed repository names
processed_repos = set()

i = 0
j = 0
for c in codes:
    try:
        r = c.repository

        if r.name in processed_repos:
            continue

        processed_repos.add(r.name)

        if detect(str(r.description)) != 'en' or r.fork or r.forks_count <= 1 or r.stargazers_count <= 1 \
                or r.get_contributors().totalCount <= 1:
            j = j + 1
            continue
        a = set()
        fileNameContents = ";".join([element.name for element in r.get_contents("/")])
        message_content = []
        comments_content = []
        commit_dates = []
        repo_total_commit_dates = []

        # list repo total commits and timestamp
        for commit in r.get_commits(sha=r.default_branch):
            repo_total_commit_dates.append(commit.commit.author.date.strftime('%Y-%m-%d %H:%M:%S'))

        # list drawio commit dates
        for commit in r.get_commits(sha=r.default_branch, path=c.path):
            message_content.append(commit.commit.message.replace('\n', ' '))
            commit_dates.append(commit.commit.author.date.strftime('%Y-%m-%d %H:%M:%S'))
            for com in commit.get_comments():
                comments_content.append(com.body.replace('\n', ' '))
            if commit.author:
                a.add(commit.author.id)
        fileChangesCommits = ";".join(message_content)
        fileChangesComments = ";".join(comments_content)
        data.append([r.name, r.html_url, r.description, r.stargazers_count, r.forks_count,
                     r.get_commits(sha=r.default_branch, path=c.path).totalCount, fileNameContents,
                     r.get_commits().totalCount,
                     r.get_contributors().totalCount, len(a),
                     r.get_watchers().totalCount, r.get_issues().totalCount,
                     r.get_releases().totalCount, r.get_pulls().totalCount, c.path, fileChangesCommits,
                     fileChangesComments, commit_dates, r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                     repo_total_commit_dates])
        results_file_name = datetime.datetime.now().strftime('%Y_%m_%d') + ".csv"
        with open(results_file_name, 'a', newline='',
                  encoding='utf-8-sig') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            if i == 0:
                writer.writerow(headers)
            writer.writerow(data[i])

            # Sleep for 10 seconds after writing a line to the CSV file
            time.sleep(1)

        print(g.get_rate_limit())
        i += 1

    except Exception as e:
        g = Github(login_or_token=get_access_token())
        print("Some repos excluded because of the reason: {}".format(str(e)))
print(j)
