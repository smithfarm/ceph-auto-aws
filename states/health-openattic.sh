#!/bin/bash
#
# Accept the local minion keys and run the "health-openattic.sh" qa script
# from the DeepSea clone

sudo salt-key -Ay
cd DeepSea/qa
sudo suites/basic/health-openattic.sh --cli
