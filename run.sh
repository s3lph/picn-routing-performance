#!/usr/bin/env bash

ulimit -t 60

for n in `seq 1 10`; do
  for interval in 0.5 1.0 2.0; do
    for run in `seq 1 20`; do
      python3.6 picn-routing-measurements.py $n 20 $interval
    done
  done
done

ulimit -t 0
