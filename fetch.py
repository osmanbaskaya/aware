import fitbit
from time import sleep
import pytz
import gather_keys_oauth2 as Oauth2
import datetime

TIMEZONE = pytz.timezone("America/Los_Angeles")


def get_client(client_id, client_secret, access_token=None, refresh_token=None):

    if access_token is None or refresh_token is None:
        server = Oauth2.OAuth2Server(client_id, client_secret)

        # TODO: better way to get the access token necessary.
        # Check here: https://community.fitbit.com/t5/Web-API-Development/Heart-rate-with-python-api/td-p/3522842
        url, _ = server.fitbit.client.authorize_token_url()
        server.browser_authorize()
        # url, _ = server.fitbit.client.authorize_token_url()
        # print(url)
        access_token = str(server.fitbit.client.session.token["access_token"])
        refresh_token = str(server.fitbit.client.session.token["refresh_token"])

    auth2_client = fitbit.Fitbit(
        client_id,
        client_secret,
        oauth2=True,
        access_token=access_token,
        refresh_token=refresh_token,
    )
    return auth2_client


def update_alarm(client, device_id, after_mins=10):
    # Update the first alarm
    alarm_id = client.get_alarms(device_id)["trackerAlarms"][0]["alarmId"]
    alarm_time = get_localized_now() + datetime.timedelta(minutes=after_mins)
    client.update_alarm(
        device_id, alarm_id, alarm_time, week_days=[], snooze_length=1, snooze_count=3
    )

    return alarm_time


def add_alarm(client, device_id, after_mins=10):
    now = datetime.datetime.now()
    alarm_time = TIMEZONE.localize(now) + datetime.timedelta(minutes=after_mins)
    client.add_alarm(device_id, alarm_time, week_days=[])


def fetch_heartrate(client):
    return client.intraday_time_series("activities/heart", detail_level="1sec")


def get_device_id(client):
    return client.get_devices()[0]["id"]


def get_last_n_heartrates(heartrate_data, n=40):
    return [e["value"] for e in heartrate_data["activities-heart-intraday"]["dataset"][-n:]]


def should_alarm(heartrates, max_heartrate_to_alarm, avg_heartrate_to_alarm):
    max_heartrate = max(heartrates)
    avg_heartrate = sum(heartrates) / len(heartrates)
    if max_heartrate >= max_heartrate_to_alarm or avg_heartrate >= avg_heartrate_to_alarm:
        return True

    return False


def get_localized_now(timezone=TIMEZONE):
    now = datetime.datetime.now()
    return timezone.localize(now)


def run():
    import argparse

    parser = argparse.ArgumentParser(description="Aware")
    parser.add_argument("--client-id", required=True, type=str)
    parser.add_argument("--secret", required=True, type=str)
    parser.add_argument("--device-id", default=None)
    parser.add_argument("--access-token", default=None)
    parser.add_argument("--refresh-token", default=None)
    parser.add_argument("--max-heartrate-to-alarm", default=95, type=int)
    parser.add_argument("--avg-heartrate-to-alarm", default=85, type=int)

    args = parser.parse_args()

    print(f"{args}")
    client = get_client(args.client_id, args.secret, args.access_token, args.refresh_token)
    device_id = args.device_id
    if device_id is None:
        device_id = get_device_id(client)

    last_alarm_time = get_localized_now() - datetime.timedelta(days=10)
    while True:
        heartrate_data = fetch_heartrate(client)
        heartrates = get_last_n_heartrates(heartrate_data, n=40)
        if len(heartrates) != 0:
            if should_alarm(
                heartrates, int(args.max_heartrate_to_alarm), int(args.avg_heartrate_to_alarm)
            ):
                # 3 hours grace period. Do not set alarm
                if (get_localized_now() - last_alarm_time).total_seconds() > 60 * 60 * 3:
                    last_alarm_time = update_alarm(client, device_id, after_mins=10)
                    print("Alarm updated.")
                else:
                    print("No need to update the alarm. Grace period")
            else:
                print("No need to update the alarm. Threshold is not exceeded.")

        sleep(120)


if __name__ == "__main__":
    run()
