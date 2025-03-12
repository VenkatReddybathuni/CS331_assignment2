#!/bin/bash


mkdir -p results

chmod +x experiments.py analyze_results.py

sudo python3 experiments.py --option=a
python3 analyze_results.py --experiment=a
sudo python3 experiments.py --option=b
python3 analyze_results.py --experiment=b
sudo python3 experiments.py --option=c
python3 analyze_results.py --experiment=c
sudo python3 experiments.py --option=d
python3 analyze_results.py --experiment=d


echo "Analyzing results "
python3 analyze_results.py --experiment=all