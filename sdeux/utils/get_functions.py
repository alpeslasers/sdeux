def get_s2_name(s2):
    return s2.get_al_identifier()


def get_s2_type(s2):
    return 'V{}'.format(s2.hw_version)


def get_pulser_info(s2):
    return {'hw_version': s2.info.hw_version,
            'sw_version': s2.info.sw_version,
            'device_id': s2.info.device_id}