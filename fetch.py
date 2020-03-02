import fitbit
import pytz
import gather_keys_oauth2 as Oauth2
import datetime

TIMEZONE = pytz.timezone("America/Los_Angeles")

# WEEKDAY = {5: "SATURDAY"}


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


def update_alarm(client, device_id, after_mins=10):
    # Update the first alarm
    now = datetime.datetime.now()
    alarm_id = client.get_alarms(device_id)["trackerAlarms"][0]["alarmId"]
    alarm_time = TIMEZONE.localize(now) + datetime.timedelta(minutes=after_mins)
    client.update_alarm(
        device_id, alarm_id, alarm_time, week_days=[], snooze_length=1, snooze_count=3
    )


def add_alarm(client, device_id, after_mins=10):
    now = datetime.datetime.now()
    alarm_time = TIMEZONE.localize(now) + datetime.timedelta(minutes=after_mins)
    client.add_alarm(device_id, alarm_time, week_days=[])


def fetch_heartrate(client):
    result = client.intraday_time_series("activities/heart")
    print(result)


def get_device_id(client):
    return client.get_devices()[0]["id"]


def run():
    import argparse

    parser = argparse.ArgumentParser(description="Aware")
    parser.add_argument("--client-id", required=True, default=64, type=str)
    parser.add_argument("--secret", required=True, default=256, type=str)
    parser.add_argument("--device-id", default=None)

    args = parser.parse_args()

    print(f"{args}")
    client = get_client(args.client_id, args.secret)
    device_id = args.device_id
    if device_id is None:
        device_id = get_device_id(client)

    fetch_heartrate(client)
    # update_alarm(client, device_id)


if __name__ == "__main__":
    run()
