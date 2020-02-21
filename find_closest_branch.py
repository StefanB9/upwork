import pandas as pd
import numpy as np
import datetime as dt
import requests

with open('./config/api-key.txt') as f:
    API_KEY = f.readline()

MT_M_CON_FACT = 0.000621371
API_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json?'


def gen_all_options():
    branches = pd.read_csv('data/csv/find_closest_branch/branches.csv')
    raw_file = pd.read_csv('data/csv/find_closest_branch/raw_file.csv')

    data = pd.DataFrame()
    count = 0
    origins = []

    for branch in branches.iterrows():
        branch_address = branch[1]['Address']
        url = branch_address + '|'
        origins.append(url)
    origins = ''.join(origins)[:-1]

    for location in raw_file.iterrows():
        location_address = location[1]['Address']
        location_city = location[1]['City']
        location_state = location[1]['State']
        location_zip = location[1]['Zip']
        count += 1
        print(location_address, location_city, location_state, location_zip, count, sep='--')
        url = API_URL + 'origins=' + origins + \
            '&destinations=' + location_address + '+' + location_city + '+' + location_state + '+' + str(location_zip) + \
            '&key=' + API_KEY
        result = requests.get(url).json()
        origin_addresses = result['origin_addresses']
        routes = result['rows']

        for i in range(len(origin_addresses)):
            distance = routes[i]['elements'][0]['distance']['value']
            duration = routes[i]['elements'][0]['duration']['value']
            temp = pd.DataFrame(dict(LOC_NUMBER=location[1]['Number'], LOC_ADDRESS=location_address,
                                LOC_CITY=location_city, LOC_STATE=location_state, LOC_ZIP=location_zip,
                                BRANCH_ADDRESS=origin_addresses[i],
                                DISTANCE=int(np.round(distance*MT_M_CON_FACT)), DRIVE_TIME=str(dt.timedelta(seconds=duration))), index=[0])
            data = pd.concat([data, temp])
    data.reset_index()
    data.to_csv('all_options.csv', index_label='INDEX')


if __name__ == "__main__":
    gen_all_options()
    all_options = pd.read_csv('data/csv/find_closest_branch/all_options.csv', index_col='INDEX')
    all_options = all_options.sort_values(by='DRIVE_TIME')
    all_options = all_options.drop_duplicates('LOC_ADDRESS')
    all_options.to_csv('data/csv/find_closest_branch/shortest_branch.csv', index=False)
