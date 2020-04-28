from time import sleep, strftime, time, gmtime, mktime

import time
st = time.time()
sleep(1)

time_test_min = int((time.time()-st)/60)
time_test_sec = int((time.time() -st)%60)
print('Execution time is: {} min {} sec'.format(time_test_min,time_test_sec))
