import getpass
import datetime
from configuration_manager import gConfig2
import ast
from stools.s2Qualification.ssrv_communication import post_results
import json

ssrv_url = gConfig2.get_url('ssrv_restless')
import requests
import pandas as pd
import datetime


if __name__ == '__main__':
    df = pd.read_csv('/home/users2/olgare/local/Temp/s2_qualif_test.csv')
    p_patch={}

    for i in range(0, df.shape[0]):
        sample_name = df['sample_name'][i]
        validator = getpass.getuser()
        firmware_version = df['firmware_version'][i]
        valid_date = '{}'.format(datetime.date.today())
        validation_passed = '{}'.format(df['is_valid'][i])
        comment = df['comment'][i]

        p_patch = {
            "validator" : validator,
            "sample_name": sample_name,
            "firmware_version":str(firmware_version),
            "valid_date":valid_date,
            "validation_passed":ast.literal_eval(validation_passed),
            "comment":comment
        }
        post_results (p_patch)


