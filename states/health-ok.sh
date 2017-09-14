#!/bin/bash
#
# Accept the local minion keys and run the "health-ok.sh" qa script
# from the DeepSea clone

sudo salt-key -Ay
cd DeepSea/qa
sudo suites/basic/health-ok.sh --cli
