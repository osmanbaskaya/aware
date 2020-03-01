import fitbit
import pytz
import gather_keys_oauth2 as Oauth2
import datetime

TIMEZONE = pytz.timezone("America/Los_Angeles")

WEEKDAY = {5: "SATURDAY"}

# client.get_devices()[0]['id']
DEVICE_ID = "883272325"


def get_client(client_id, client_secret):
    server = Oauth2.OAuth2Server(client_id, client_secret)

    # TODO: better way to get the access token necessary.
    # Check here: https://community.fitbit.com/t5/Web-API-Development/Heart-rate-with-python-api/td-p/3522842
    server.browser_authorize()
    # url, _ = server.fitbit.client.authorize_token_url()
    # print(url)
    ACCESS_TOKEN = str(server.fitbit.client.session.token["access_token"])
    REFRESH_TOKEN = str(server.fitbit.client.session.token["refresh_token"])
    auth2_client = fitbit.Fitbit(
        client_id,
        client_secret,
        oauth2=True,
        access_token=ACCESS_TOKEN,
        refresh_token=REFRESH_TOKEN,
    )
    return auth2_client


def update_alarm(client, after_mins=10):
    # Update the first alarm
    now = datetime.datetime.now()
    alarm_id = client.get_alarms(DEVICE_ID)["trackerAlarms"][0]["alarmId"]
    alarm_time = TIMEZONE.localize(now) + datetime.timedelta(minutes=after_mins)
    client.update_alarm(
        DEVICE_ID, alarm_id, alarm_time, week_days=[], snooze_length=1, snooze_count=3
    )


def add_alarm(client, after_mins=10):
    now = datetime.datetime.now()
    alarm_time = TIMEZONE.localize(now) + datetime.timedelta(minutes=after_mins)
    client.add_alarm(DEVICE_ID, alarm_time, [WEEKDAY[alarm_time.weekday()]])


def fetch_heartrate(client):
    result = client.intraday_time_series("activities/heart")
    print(result)


def run():
    import argparse

    parser = argparse.ArgumentParser(description="Aware")
    parser.add_argument("--client-id", default=64, type=str)
    parser.add_argument("--secret", default=256, type=str)

    args = parser.parse_args()

    print(f"{args}")
    client = get_client(args.client_id, args.secret)
    fetch_heartrate(client)
    # update_alarm(client)


if __name__ == "__main__":
    run()
