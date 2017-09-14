#!/bin/bash
sudo salt-key -Ay
cd DeepSea/qa
sudo suites/basic/health-ok.sh --cli
