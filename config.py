import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
TIMEZONE = "Europe/Prague"


def _parse_app(env_var, alias):
    number, typ, year = os.environ[env_var].split(",")
    return {"number": number, "type": typ, "year": year, "alias": alias}


APPLICATIONS = [
    _parse_app("APP_TRV", "TRV"),
    _parse_app("APP_WRK", "WRK"),
    _parse_app("APP_OLD", "OLD"),
]
