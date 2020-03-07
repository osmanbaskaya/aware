import fitbit
from time import sleep
import pytz
import gather_keys_oauth2 as Oauth2
import fitbit.exceptions
import datetime
import requests
import base64

TIMEZONE = pytz.timezone("America/Los_Angeles")


class FitBitClient:
    def __init__(self, client_id, client_secret, access_token=None, refresh_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.auth2_client = None
        self.client_create_or_refresh()

    def client_create_or_refresh(self):
        # refresh if client is already created.
        if self.auth2_client is not None:
            encoded = base64.b64encode(f"{self.client_id}:{self.client_secret}").decode("utf8")
            headers = {
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            body = {"grant_type": "refresh_token", "refresh_token": self.refresh_token}
            r = requests.post(
                "https://api.fitbit.com/oauth2/token", headers=headers, data=body
            ).json()
            self.access_token = r["access_token"]
            self.refresh_token = r["refresh_token"]

        self.auth2_client = fitbit.Fitbit(
            self.client_id,
            self.client_secret,
            oauth2=True,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
        )

    def do_client_request(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except fitbit.exceptions.HTTPUnauthorized:
            self.client_create_or_refresh()
            return self.do_client_request(func, *args, **kwargs)

    def update_alarm(self, device_id, after_mins=10):
        # Update the first alarm
        func = self.auth2_client.get_alarms
        alarm_id = self.do_client_request(func, device_id)["trackerAlarms"][0]["alarmId"]

        alarm_time = get_localized_now() + datetime.timedelta(minutes=after_mins)

        func = self.auth2_client.update_alarm
        self.do_client_request(func,
            device_id, alarm_id, alarm_time, week_days=[], snooze_length=1, snooze_count=3
        )

        return alarm_time

    def add_alarm(self, device_id, after_mins=10):
        now = datetime.datetime.now()
        alarm_time = TIMEZONE.localize(now) + datetime.timedelta(minutes=after_mins)
        func = self.auth2_client.add_alarm
        self.do_client_request(func, device_id, alarm_time, week_days=[])

    def fetch_heartrate(self):
        func = self.auth2_client.intraday_time_series
        return self.do_client_request(func, "activities/heart", detail_level="1sec")

    def get_device_id(self):
        func = self.auth2_client.get_devices
        return self.do_client_request(func)[0]["id"]


def get_last_n_heartrates(heartrate_data, n=40):
    return [e["value"] for e in heartrate_data["activities-heart-intraday"]["dataset"][-n:]]


def should_alarm(heartrates, max_heartrate_to_alarm, avg_heartrate_to_alarm):
    max_heartrate = max(heartrates)
    avg_heartrate = sum(heartrates) / len(heartrates)
    print(f"Max heartrate: {max_heartrate}, Avg. heartrate: {avg_heartrate}")
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
    client = FitBitClient(args.client_id, args.secret, args.access_token, args.refresh_token)
    device_id = args.device_id
    if device_id is None:
        device_id = client.get_device_id()

    last_alarm_time = get_localized_now() - datetime.timedelta(days=10)
    while True:
        heartrate_data = client.fetch_heartrate()
        heartrates = get_last_n_heartrates(heartrate_data, n=40)
        if len(heartrates) != 0:
            if should_alarm(
                heartrates, int(args.max_heartrate_to_alarm), int(args.avg_heartrate_to_alarm)
            ):
                # 3 hours grace period. Do not set alarm
                if (get_localized_now() - last_alarm_time).total_seconds() > 60 * 60 * 3:
                    last_alarm_time = client.update_alarm(device_id, after_mins=10)
                    print("Alarm updated.")
                else:
                    print("No need to update the alarm. Grace period")
            else:
                print("No need to update the alarm. Threshold is not exceeded.")

        sleep(120)


if __name__ == "__main__":
    run()
