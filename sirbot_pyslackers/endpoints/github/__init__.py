import os
import logging

from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)
CHANNEL = os.environ.get("SLACK_GITHUB_HOOK_CHANNEL") or "community_projects"


def create_endpoints(plugin):
    plugin.router.add(issues_opened, "issues", action="opened")
    plugin.router.add(issues_closed, "issues", action="closed")
    plugin.router.add(issues_reopened, "issues", action="reopened")

    plugin.router.add(pr_opened, "pull_request", action="opened")
    plugin.router.add(pr_closed, "pull_request", action="closed")
    plugin.router.add(pr_reopened, "pull_request", action="reopened")

    plugin.router.add(release_created, "release", action="published")
    plugin.router.add(repo_created, "repository", action="created")
    plugin.router.add(repo_deleted, "repository", action="deleted")


async def _issues_message(event, app, color="good"):
    msg = Message()
    msg["channel"] = CHANNEL
    msg["attachments"] = [
        {
            "fallback": "issue {}".format(event.data["action"]),
            "color": color,
            "text": "*<{url}|{title}>*\n{body}".format(
                url=event.data["issue"]["html_url"],
                title=event.data["issue"]["title"],
                body=event.data["issue"]["body"],
            ),
            "title": "Issue {action} in <{repo_url}|{name}>".format(
                repo_url=event.data["repository"]["html_url"],
                name=event.data["repository"]["name"],
                action=event.data["action"],
            ),
            "author_icon": event.data["sender"]["avatar_url"],
            "author_name": event.data["sender"]["login"],
            "author_link": event.data["sender"]["html_url"],
            "footer": ", ".join(
                label["name"] for label in event.data["issue"]["labels"]
            ),
            "mrkdwn_in": ["text"],
        }
    ]
    await app.plugins["slack"].api.query(methods.CHAT_POST_MESSAGE, data=msg)


async def _pr_message(event, app, color="good", action=None):
    msg = Message()
    msg["channel"] = CHANNEL
    msg["attachments"] = [
        {
            "fallback": "pull request {}".format(event.data["action"]),
            "color": color,
            "text": "*<{url}|{title}>*\n{body}".format(
                url=event.data["pull_request"]["html_url"],
                title=event.data["pull_request"]["title"],
                body=event.data["pull_request"]["body"],
            ),
            "title": "Pull request {action} in <{repo_url}|{name}>".format(
                repo_url=event.data["repository"]["html_url"],
                name=event.data["repository"]["name"],
                action=action or event.data["action"],
            ),
            "author_icon": event.data["sender"]["avatar_url"],
            "author_name": event.data["sender"]["login"],
            "author_link": event.data["sender"]["html_url"],
            "footer": "+ {add} / - {del_}".format(
                add=event.data["pull_request"]["additions"],
                del_=event.data["pull_request"]["deletions"],
            ),
            "mrkdwn_in": ["text"],
        }
    ]
    await app.plugins["slack"].api.query(methods.CHAT_POST_MESSAGE, data=msg)


async def issues_opened(event, app):
    await _issues_message(event, app, "good")


async def issues_closed(event, app):
    await _issues_message(event, app, "danger")


async def issues_reopened(event, app):
    await _issues_message(event, app, "good")


async def pr_opened(event, app):
    await _pr_message(event, app, "good")


async def pr_closed(event, app):
    if event.data["pull_request"]["merged"]:
        await _pr_message(event, app, "#6f42c1", action="merged")
    else:
        await _pr_message(event, app, "danger")


async def pr_reopened(event, app):
    await _pr_message(event, app, "good")


async def release_created(event, app):
    msg = Message()
    msg["channel"] = CHANNEL
    msg["text"] = "Release {release} created in {repo} by {user}".format(
        release=event.data["release"]["tag_name"],
        repo=event.data["repository"]["name"],
        user=event.data["sender"]["login"],
    )
    await app.plugins["slack"].api.query(methods.CHAT_POST_MESSAGE, data=msg)


async def repo_created(event, app):
    msg = Message()
    msg["channel"] = CHANNEL
    msg["text"] = "Repository {repo} created by {user} :tada:".format(
        repo=event.data["repository"]["name"], user=event.data["sender"]["login"]
    )
    await app.plugins["slack"].api.query(methods.CHAT_POST_MESSAGE, data=msg)


async def repo_deleted(event, app):
    msg = Message()
    msg["channel"] = CHANNEL
    msg["text"] = "Repository {repo} deleted by {user} :cold_sweat:".format(
        repo=event.data["repository"]["name"], user=event.data["sender"]["login"]
    )
    await app.plugins["slack"].api.query(methods.CHAT_POST_MESSAGE, data=msg)
