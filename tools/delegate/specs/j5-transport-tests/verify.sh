#!/usr/bin/env bash
set -e
python -I tools/hd-models/tests/test_j5_transport_1.py
python -I tools/hd-models/tests/test_j5_transport_2.py
python -I tools/hd-models/tests/test_studio_transport.py
