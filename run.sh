#!/usr/bin/env bash

timestamp="$(date -u +%s)"

for n in `seq 1 10`; do
  for interval in 0.5 1.0 2.0; do
    for run in `seq 1 20`; do
        timeout -k 5s -s TERM "$((10+5*$n))s" env PYTHONPATH="$(realpath ./picn)" python3.6 picn-routing-measurements.py $timestamp $n $interval $run
    done
  done
done

python3.6 plot.py $timestamp
