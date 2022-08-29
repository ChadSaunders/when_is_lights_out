import pandas as pd
import tweepy
import requests
import time
import zulu
import emoji


def get_current_f1_api():
    # F1 API
    url = "http://ergast.com/api/f1/current"
    payload = {}
    headers = {}
    response = requests.request("GET",
                                url + '.json',  # Returns data in json format
                                headers=headers,
                                data=payload).json()  # Parses data into json object
    return response


def get_tweet_string(race_info):
    tweet_limit = 280
    day_of_week = ['Monday',
                   'Tuesday',
                   'Wednesday',
                   'Thursday',
                   'Friday',
                   'Saturday',
                   'Sunday']

    t_race_name = race_info['raceName']
    t_round = race_info['round']
    t_season = race_info['season']
    t_quali_zulu = zulu.parse(race_info['Qualifying']['date'] +
                              ' ' +
                              race_info['Qualifying']['time'][0:-1])
    t_quali_day = day_of_week[t_quali_zulu.isoweekday() - 1]
    t_quali_time = t_quali_zulu.format('HH:mm',
                                       tz='local')
    t_race_time = zulu.parse(race_info['date'] +
                             ' ' +
                             race_info['time'][0:-1]).format('HH:mm',
                                                             tz='local')
    t_circuit = race_info['Circuit']['circuitName']

    # Create strings
    intro = f'Round {t_round} in the {t_season} season is the {t_race_name} at the {t_circuit}.'
    pre_race_events = f'Qualifying is at {t_quali_time} {t_quali_day}.'

    # Add sprint race info
    if 'Sprint' in race_info:
        t_sprint_zulu = zulu.parse(race_info['Sprint']['date'] +
                                   ' ' +
                                   race_info['Sprint']['time'][0:-1])
        t_sprint_day = day_of_week[t_sprint_zulu.isoweekday() - 1]
        t_sprint_time = t_sprint_zulu.format('HH:mm',
                                             tz='local')
        # append info to string
        pre_race_events = f'{pre_race_events} The sprint race is at {t_sprint_time} {t_sprint_day}.'

    tweet = f'{intro} {pre_race_events} 🚦 LIGHTS OUT IS AT {t_race_time} Sunday! 🚦 (UK times)'

    # Check tweet length
    if len(tweet) > tweet_limit:
        # Remove circuit info
        intro = f'Round {t_round} in the {t_season} season is the {t_race_name}.'
        tweet = f'{intro} {pre_race_events} LIGHTS OUT IS AT {t_race_time} Sunday! (UK times)'
        if len(tweet) > tweet_limit:
            print(f'WARNING: Tweet length over {tweet_limit} character limit')

    return tweet


def configure_twitter_api():
    # Get Twitter API keys
    keys = pd.read_csv('keys.csv')
    api_key = keys['Key_Value'][0]
    api_key_secret = keys['Key_Value'][1]
    access_token = keys['Key_Value'][3]
    access_token_secret = keys['Key_Value'][4]

    # Authenticate to Twitter
    auth = tweepy.OAuthHandler(api_key, api_key_secret)
    auth.set_access_token(access_token, access_token_secret)

    # Create API object
    api_twitter = tweepy.API(auth)

    return api_twitter


if __name__ == '__main__':
    """
    This script will connect with an api to retrive F1 race information. It will then tweet on a Thursday the time the 
    race starts. It will also tweet a reminder one hour before the race
    """
    # Construct Twitter API
    api = configure_twitter_api()

    # Get F1 data
    f1_json = get_current_f1_api()
    f1_json_races = f1_json['MRData']['RaceTable']['Races']

    # Check current date
    today = zulu.now()

    # Extract data for next race
    for race in f1_json_races:
        # Get race date
        race_date = zulu.parse(race['date'] +
                               ' ' +
                               race['time'][0:-1])

        # Check if race has passed
        if race_date < today:
            print(f'{race["raceName"]} on {race_date} has already passed')
            continue

        # Once the next race is found
        print(f'Next race is {race["raceName"]} on {race_date}')

        # Time based work
        seconds_to = {}
        seconds_to['race'] = int(today.time_to(race_date,
                                               threshold=604800,
                                               granularity='second').split(' ')[1])
        seconds_to['hour_before_race'] = seconds_to['race'] - (60 * 60)
        seconds_to['three_days_before_race'] = seconds_to['race'] - (60 * 60 * 24 * 3)

        # Sleep until three days before race
        if seconds_to['three_days_before_race'] > 0:
            print(f'sleeping script at {today} for {seconds_to["three_days_before_race"]} seconds')
            time.sleep(seconds_to['three_days_before_race'])

            # Construct tweet
            tweet_string = get_tweet_string(race)
            print(f'tweet string: "{tweet_string}"')

            # Create a tweet
            api.update_status(tweet_string)

        # 1 Hour race warning
        if seconds_to['hour_before_race'] > 0:
            # Sleep until 1 hour before
            print(f'sleeping script at {today} for {seconds_to["hour_before_race"]} seconds')
            time.sleep(seconds_to['hour_before_race'])

            # Construct reminder
            reminder_string = '🚦ONE HOUR UNTIL LIGHTS OUT🚦'
            api.update_status(reminder_string)

    print('Season finished - Script ending')
