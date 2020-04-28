import json

import requests
import getpass
from configuration_manager import gConfig2

ssrv_url = gConfig2.get_url('ssrv_restless')

# DATA = {"applied_voltage": None,
#         "test_scope": None,
#         "applied_voltage_a": None,
#         "applied_voltage_b": None,
#         "current": None,
#         "voltage": None,
#         "pulser_info": None,  # TODO: check what for
#         "pulse_mode": None,
#         "duty_cycle": None,
#         "pulse_length": None,
#         "pulse_delay": None,
#         "s2_wf_amplitude": None,
#         "s2_wf_duty": None,
#         "s2_wf_negative_width": None,
#         "s2_wf_delay": None,
#         "s2_wf_period": None,
#         "s2_wf_trac_t": None,
#         "s2_wf_trac_v": None,
#         "ref_wf_amplitude": None,
#         "ref_wf_duty": None,
#         "ref_wf_negative_width": None,
#         "ref_wf_period": None,
#         "ref_wf_trac_t": None,
#         "ref_wf_trac_v": None,
#         "IN_ARM": None,
#         "IN_SAFETY": None,
#         "MCU_OUT_INT": None,
#         "INTERLOCK": None,
#         "IN_MOD_DIR": None,
#         "GND": None
#         }


def save_measurement(s2_sample_name, measurement_data, measure_type='s2_pulse'):
    rsp = requests.post(ssrv_url + '/measures',
                        params={'sample_name': s2_sample_name,
                                'session_type': 's2_pulse_char',
                                'measure_type': measure_type,
                                'station_name': 'S2',
                                'setup_name': 'pulse_char',
                                'user_name': getpass.getuser()},
                        json={'data': measurement_data})

    rsp.raise_for_status()
    d = rsp.json()
    print(d)


def post_results(p_patch, result_type = 's2_qualif'):
    rsp = requests.post(ssrv_url + '/results/resources/{}'.format(result_type),
                        json={'data': p_patch})
    rsp.raise_for_status()
    return rsp.json()['pk'][0]



def check_sample_in_db(sample_name, type):
    rsp = requests.get(ssrv_url + '/samples',
                   params={'filters': json.dumps([{'name': 'name',
                                                   'op': 'eq',
                                                   'val': sample_name}])})
    d = rsp.json()

    if d['num_results'] == 0:
        rsp = requests.post(ssrv_url + '/samples',
                            params={'name': sample_name,
                                    'sample_type': 'S2:{}'.format(type),
                                    'fullname': sample_name})
        rsp.raise_for_status()
