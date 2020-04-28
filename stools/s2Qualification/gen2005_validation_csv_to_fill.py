import getpass
import datetime
from configuration_manager import gConfig2
import ast
from elbit_scripts.s2Qualification.ssrv_communication import post_results
import json

ssrv_url = gConfig2.get_url('ssrv_restless')
import requests
import pandas as pd
from datetime import datetime, timedelta

if __name__ == '__main__':
    t= datetime.now()
    interval_days = int(input("Please enter the time interval (in days) for measurements you want to retrieve (ex. 15 = last 15 days): "))
    firmware_version = input("Please enter the firmware version (ex. 3830): ")
    measurement_interval =t-timedelta(days=interval_days)
    rsp = requests.get(gConfig2.get_url('ssrv_restless') + '/samples',
                       params={'filters': json.dumps([{'name': 'sample_type',
                                                       'op': 'like',
                                                       'val': 'S2%'},
                                                      {'name': 'last_measurement_added',
                                                       'op': '>',
                                                       'val': measurement_interval.isoformat()}
                                                      ]),   })
    data = rsp.json()
    report = []
    for d in data['objects']:
        added = d['last_measurement_added']
        id = d['id']
        name = d['name']
        data_to_report = {'id': id,
                          'last_measurement_added': added,
                          'sample_name': name,
                          'is_valid': '',
                          'firmware_version':int(firmware_version),
                          'comment': ''}
        report.append(data_to_report)

    df = pd.DataFrame.from_records(report)
    df.to_csv('/home/users2/olgare/local/Temp/s2_qualif_test.csv', float_format="%.2f")




