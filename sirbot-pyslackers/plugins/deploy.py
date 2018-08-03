import os
import logging

from slack import methods
from aiohttp.web import Response

LOG = logging.getLogger(__name__)
DEPLOY_CHANNEL = "community_projects"
DEPLOY_TOKEN = os.environ["DEPLOY_TOKEN"]


class DeployPlugin:
    __name__ = "deploy"

    def __init__(self):
        self.session = None

    def load(self, sirbot):
        self.session = sirbot.http_session
        sirbot.router.add_route("POST", "/pyslackers/deploy", deploy)


async def deploy(request):
    payload = await request.json()

    if payload.get("token") == DEPLOY_TOKEN:
        await request.app.plugins["slack"].api.query(
            url=methods.CHAT_POST_MESSAGE,
            data={
                "channel": DEPLOY_CHANNEL,
                "text": f"""Successfully deployed {payload["item"]}"""
                f"""(<{payload["repo"]}/commit/{payload["version"]}|{payload["version"][:7]}>) :tada: !""",
            },
        )

    return Response(status=200)
