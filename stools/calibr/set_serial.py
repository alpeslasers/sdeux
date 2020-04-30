#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import argparse

from stools.gen2005 import S2
from stools.serial_handler import S2SerialHandler

from stools.calibr.s2_cal_db import get_board, copy_board
from stools.calibr.s2_local_settings import s2_port_name

logger = logging.getLogger(__name__)

__author__ = 'gregory'
__copyright__ = "Copyright 2018, Alpes Lasers SA"

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=s2_port_name)
    parser.add_argument("--qcl", action='store_const', const=True, default=False)
    args = parser.parse_args()

    sh = S2SerialHandler(args.port)
    sh.open()
    try:
        s2 = S2(sh)
        s2.set_up()
        old_sn = s2.info.device_id
        sn = None
        qcl_sn = b''
        if args.qcl:
            print('Numero du module laser actuel : {}'.format(s2.info.laser_id))
            while not qcl_sn:
                try:
                    dat = input('Entrez le numero de serie du laser / HHL: ')
                    qcl_sn = dat.encode()
                    if len(qcl_sn) > 8:
                        qcl_sn = b''
                        raise ValueError
                except Exception:
                    print('Numero de serie invalide')
            s2.set_configuration(laser_id=qcl_sn)
            s2.reload_info()
            print('Nouveau numero du module laser : {}'.format(s2.info.laser_id))
        else:
            while sn is None:
                try:
                    dat = input('Entrez le nouveau numero de serie du S-2: ')
                    sn = int(dat)
                    if not 0 < sn < 2**32-2:
                       sn = None
                       raise ValueError
                    if get_board(sn):
                        overwrite = input("Le S-2 #{} existe déjà, êtes-vous sûr? [y/N] ".format(sn)) in 'yY'
                        if not overwrite:
                            sn = None
                except Exception:
                    print('Numero de serie invalide')

            s2.set_configuration(device_id=sn)
            if get_board(old_sn):
                copy_board(old_sn, sn, overwrite=True)
                input("Le S-2 #{} a été copié sur le nouveau #{} sur s2admin.\n"
                      "Il est de votre responsabilité de supprimer (ou non) les entrées reliées à l'ancien numéro de série"
                      " #{} en allant sur s2admin\n(Appuyez sur une touche pour continuer...)".format(old_sn, sn, old_sn))
    finally:
        sh.close()
