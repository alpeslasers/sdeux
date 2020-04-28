import slumber
# from logging import info

api = slumber.API("http://s2admin.internal.alp/api",
                  auth=("calibration_script", '924ht536g36tvSX'))


def get_board(board_sn):
    ret = api.s2.get(serial_number=board_sn)
    if len(ret) == 0:
        return None
    ret_itm = ret[0]
    # info('board id: {}'.format(ret_itm['id']))
    return ret_itm


def get_calibration(board_sn):
    ret = api.s2calibration.get(item__serial_number=board_sn)
    if len(ret) == 0:
        return None
    ret_itm = ret[0]
    # info('cal id: {}'.format(ret_itm['id']))
    return ret_itm


def copy_board(board_sn, new_board_sn, overwrite=False):
    board = get_board(board_sn)
    new_brd = get_board(new_board_sn)
    if board is None:
        raise ValueError('No board with serial "{}"'.format(board_sn))
    if new_brd:
        if not overwrite:
            raise ValueError('Board #{} already exists'.format(new_board_sn))
        board['serial_number'] = new_board_sn
        board['id'] = new_brd['id']
        write_board(board)
        new_brd = board
    else:
        board['serial_number'] = new_board_sn
        del board['id']
        new_brd = api.s2.post(board)

    cal = get_calibration(board_sn)
    if cal:
        new_cal = get_calibration(new_board_sn)
        if new_cal is None:
            new_cal = create_calibration(new_board_sn)
        for k in ['vout_meas_a', 'vout_meas_b', 'vout_set_a', 'vout_set_b', 'calibrated_at', 'i_a', 'i_b']:
            new_cal[k] = cal[k]
        write_calibration(new_cal)
    return new_brd


def create_board(board_sn):
    new_brd = api.s2.post({'serial_number': board_sn})
    return new_brd


def create_calibration(board_sn):
    brd = get_board(board_sn)
    if brd is None:
        brd = create_board(board_sn)
    new_cal = api.s2calibration.post({'item': brd['id']})
    return new_cal


def write_board(brd):
    api.s2(brd['id']).put(brd)


def write_calibration(cal):
    api.s2calibration(cal['id']).put(cal)


def upload_firmware(rev, file_name, version_number, api_version):
    with open(file_name, 'rb') as fp:
        return api.s2firmware.post({
            'version': version_number,
            'hardware_revision': rev,
            'api_version': api_version},
            files={'binary_file': fp})


# # this is done by jenkins now
# def upload_software(file_name, platform, version_number, api_version):
#     with open(file_name, 'rb') as fp:
#         return api.s2ui.post({'version': version_number,
#                               'platform': platform,
#                               'api_version': api_version},
#                              files={'binary_file': fp})

