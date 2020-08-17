# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)

__author__ = 'gregory'
__copyright__ = "Copyright 2018, Alpes Lasers SA"

S2_CURR_LIMIT_MODE_GLOBAL = 0
S2_CURR_LIMIT_MODE_STORED = 1

S2_PULSING_OFF = 0
S2_PULSING_INTERNAL = 1
S2_PULSING_FULL_EXTERNAL = 2
S2_PULSING_EXTERNAL = 2
S2_PULSING_BURST = 3
S2_PULSING_MODE_A = 4
S2_PULSING_MODE_B = 5
S2_PULSING_BURST_EXTERNAL_TRIGGER = 6
S2_PULSING_BURST_EXTERNAL = 6
S2_PULSING_EXTERNAL_TRIGGER = 7
S2_PULSING_MODE_AB = 8
S2_PULSING_MODE_B4 = 9
S2_PULSING_MODE_B6 = 10
S2_PULSING_MODE_B8 = 11
S2_PULSING_MODE_CSS = 12
S2_PULSING_MODE_CST = 13
S2_PULSING_INTERNAL_FAST = 14

S2_PACKET_INFO = 0
S2_PACKET_QUERY_SETTINGS = 1
S2_PACKET_SET_SETTINGS = 2
S2_PACKET_BOOTLOADER = 3
S2_PACKET_SET_PERSISTENT_SETTINGS = 4
S2_PACKET_RESET_STATUS_FLAG = 5
S2_PACKET_UPTIME = 6
S2_PACKET_STORE_CALIBRATION = 7
S2_PACKET_SET_CALIBRATION = 8
S2_PACKET_QUERY_CALIBRATION = 9
S2_PACKET_SET_ADVANCED_SETTINGS = 10
S2_PACKET_ADVANCED_INFO = 11
S2_PACKET_DEBUG_INFO = 12
S2_PACKET_SET_CONFIGURATION = 13
S2_PACKET_SET_FAST_PRESET = 14
S2_PACKET_QUERY_CONFIGURATION = 15
S2_PACKET_QUERY_BIT = 20

S2_STATUS_OK = 0
S2_STATUS_UNDERVOLTAGE = 1
S2_STATUS_OVERCURRENT = 2
S2_STATUS_OVERVOLTAGE = 4
S2_STATUS_OVERTEMP = 8

S2_OPTION_TEMPERATURE_MONITOR = 0x01
S2_OPTION_ALT_EXT_INPUT = 0x02
S2_OPTION_SPECIAL_BURST_MODES = 0x04
S2_OPTION_NO_INTERNAL_CURRENT_LIMIT = 0x08