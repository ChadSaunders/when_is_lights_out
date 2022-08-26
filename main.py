import pandas as pd
import tweepy
import requests
# from datetime import date
import zulu


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
    t_race_name = race_info['raceName']
    t_round = race_info['round']
    t_season = race_info['season']
    t_quali_time = zulu.parse(race_info['Qualifying']['date'] +
                              ' ' +
                              race_info['Qualifying']['time'][0:-1]).format('HH:mm dd/MM',
                                                                            tz='local')
    t_race_time = zulu.parse(race_info['date'] +
                             ' ' +
                             race_info['time'][0:-1]).format('HH:mm',
                                                             tz='local')
    t_circuit = race_info['Circuit']['circuitName']

    # Create strings
    intro = f'Round {t_round} in the {t_season} season is the {t_race_name} at the {t_circuit}.'
    pre_race_events = f'Qualifying is at {t_quali_time}.'

    # Add sprint race info
    if 'Sprint' in race_info:
        t_sprint_time = zulu.parse(race_info['Sprint']['date'] +
                                   ' ' +
                                   race_info['Sprint']['time'][0:-1]).format('HH:mm dd/MM',
                                                                             tz='local')
        # append info to string
        pre_race_events = f'{pre_race_events} The sprint race is at {t_sprint_time}.'

    tweet = f'{intro} {pre_race_events} LIGHTS OUT IS AT {t_race_time} Sunday! (UK times)'

    # TODO - Add emojis into tweet (country flag).

    # TODO - Have main tweets on a Thursday and reminders for quali, sprint, and final race

    return tweet


# Get Twitter API keys
keys = pd.read_csv('keys.csv')
API_Key = keys['Key_Value'][0]
API_Key_Secret = keys['Key_Value'][1]
Access_Token = keys['Key_Value'][3]
Access_Token_Secret = keys['Key_Value'][4]

# Authenticate to Twitter
auth = tweepy.OAuthHandler(API_Key, API_Key_Secret)
auth.set_access_token(Access_Token, Access_Token_Secret)

# Create API object
api = tweepy.API(auth)

# Get F1 data
f1_json = get_current_f1_api()
f1_json_races = f1_json['MRData']['RaceTable']['Races']

# Check current date
today = zulu.now()
for race in f1_json_races:
    # Get race date
    race_date = zulu.parse(race['date'])

    if race_date > today:
        next_race = race
        break
    else:
        race_name = race['raceName']
        print(f'{race_name} on {race_date} has already passed')

# Construct tweet
tweet_string = get_tweet_string(next_race)
print(tweet_string)

print('pause')
# Create a tweet
api.update_status(tweet_string)
