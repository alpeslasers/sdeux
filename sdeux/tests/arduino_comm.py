
from dms.utils.socket_helpers import StreamSocket

if __name__ == '__main__':
    s = StreamSocket('remserial://cyclonix10.internal.alp:49085',
                    timeout=10,
                    persistent=False,
                    recv_terminator='\r\n',
                    send_terminator='\n', verbose=False, encoding='utf-8')
    s.open()
    try:
        # print(s.query('IN_ARM_OFF'))
        # print(s.query('IN_SAFETY_ON'))

        print(s.write('IN_ARM_ON'))
        import time
        time.sleep(1)
        print(s.write('IN_SAFETY_ON'))
        time.sleep(1)
    finally:
        s.close()
