import os

ANNOUCEMENTS_CHANNEL = os.environ.get("SLACK_ANNOUCEMENTS_CHANNEL") or "annoucements"
ADMIN_CHANNEL = os.environ.get("SLACK_ADMIN_CHANNEL") or "G1DRT62UC"

HELP_FIELD_DESCRIPTIONS = [
    {
        "title": "@sir_botalot hello",
        "value": f"Say hello to sir_botalot.",
        "short": True,
    },
    {
        "title": "/report",
        "value": "Report an offending user to the admin team.",
        "short": True,
    },
    {
        "title": "/gif search terms",
        "value": "Search for a gif on giphy.com .",
        "short": True,
    },
    {
        "title": "/pypi search terms",
        "value": "Search for packages on pypi.org .",
        "short": True,
    },
    {"title": "/sponsors", "value": "Referal links from our sponsors.", "short": True},
    {
        "title": "/snippet",
        "value": "Instruction on creating a slack code snippet.",
        "short": True,
    },
    {
        "title": "/howtoask",
        "value": "Prompt and referrals for how to ask a good question",
        "short": True,
    },
    {
        "title": "/justask",
        "value": "Prompt to tell just to ask a question",
        "short": True,
    },
    {
        "title": "/resources",
        "value": "Share resources for new python developers",
        "short": True,
    },
    {
        "title": "g#user/repo",
        "value": "Share the link to that github repo. User default to `pyslackers`.",
    },
    {
        "title": "s$TICKER",
        "value": "Retrieve today's prices for the provided stock ticker.",
    },
    {
        "title": "s$^INDEX",
        "value": "Retrieve today's prices for the provided stock market index (as supported by Yahoo!).",
    },
    {
        "title": "c$CRYPTO_SYMBOL",
        "value": "Retrieve today's value for the provided cryptocurrency.",
    },
]
