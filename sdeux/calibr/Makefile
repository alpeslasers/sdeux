.PHONY: all boot test run write rewrite

scmd = stm32flash -b 38400 /dev/tty.CHIPIX-AL_FTV8G4AG

5: boot1 test1 write_5 run1 set rewrite boot2 test2 run2

2005: boot1 test1 write_2005 run1 set rewrite boot2 test2 run2

boot%:
	python3 s2.py --boot
	sleep 1

test%:
	$(scmd) | true
	sleep 1

run%:
	$(scmd) -g 0
	sleep 1

write_5:
	$(scmd) -w s2_5_signed.bin

write_2005:
	$(scmd) -w s2_2005_signed.bin

set:
	python3 s2.py

rewrite:
	python3 s2.py --rewrite
	sleep 1

calibrate:
	@python3 confirmation.py "Calibration VOLTAGE. Attention au branchement. Continuer ? [y/N] "
	python3 s2.py --calibrate voltage
	@python3 confirmation.py "Calibration COURANT. Attention au branchement. Continuer ? [y/N] "
	python3 s2.py --calibrate current
	python3 s2.py --rewrite
	sleep 1

new_2005:
	$(scmd) -w s2_2005_signed.bin || $(scmd) -w s2_2005_signed.bin || $(scmd) -w s2_2005_signed.bin
	$(scmd) -g 0
	sleep 1
	@python3 set_serial.py
	@python3 confirmation.py "Calibration VOLTAGE. Attention au branchement. Continuer ? [y/N] "
	python3 s2.py --calibrate voltage
	@python3 confirmation.py "Calibration COURANT. Attention au branchement. Continuer ? [y/N] "
	python3 s2.py --calibrate current
	python3 s2.py --rewrite
	sleep 1
	python3 s2.py --reset uptimes
	@echo "New S-2m in service."

new_5:
	$(scmd) -w s2_5_signed.bin || $(scmd) -w s2_5_signed.bin || $(scmd) -w s2_5_signed.bin
	$(scmd) -g 0
	sleep 1
	@python3 confirmation.py "Calibration VOLTAGE. Attention au branchement. Continuer ? [y/N] "
	python3 s2.py --calibrate voltage
	@python3 confirmation.py "Calibration COURANT. Attention au branchement. Continuer ? [y/N] "
	python3 s2.py --calibrate current
	python3 s2.py --rewrite
	sleep 1
	python3 s2.py --reset uptimes
	@echo "New S-2 in service."
