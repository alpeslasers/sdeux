import getpass
import datetime
from configuration_manager import gConfig2
import ast
from elbit_scripts.s2Qualification.ssrv_communication import post_results
import json

ssrv_url = gConfig2.get_url('ssrv_restless')


if __name__ == '__main__':
    validator = getpass.getuser()
    sample_name = input("Hello, {}, please enter S2 Sample Name from SSRV (ex. S2-V2005-89): ".format(validator))
    firmware_version = input("Please enter the firmware version (ex. 3830): ")
    valid_date = '{}'.format(datetime.date.today())
    validation_passed = ast.literal_eval(input("S2 validation passed (True/False): "))
    comment = ''
    if not validation_passed:
        comment = input("Why the validation failed ?: ")

    p_patch = {
        "validator" : validator,
        "sample_name": sample_name,
        "firmware_version":firmware_version,
        "valid_date":valid_date,
        "validation_passed":validation_passed,
        "comment":comment
    }
    post_results (p_patch)



