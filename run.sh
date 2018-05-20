#!/usr/bin/env bash

timestamp="$(date -u +%s)"

for case in depth breadth depth_rand breadth_rand; do
  for n in `seq 1 10`; do
    for interval in 0.5 1.0 2.0; do
      for run in `seq 1 20`; do
        timeout -k 5s -s TERM "$((5+10*$n))s" env PYTHONPATH="$(realpath ./picn)" \
                python3.6 picn-routing-measurements.py $timestamp $case $run $n $interval \
            || echo Timeout
      done
    done
  done
done

for case in repo_hopping repo_hopping_edge_traverse; do
  for routing_interval in 0.1 1.0 2.0; do
    for hopping_interval in 5.0 10.0 20.0; do
      for lease_time in 0.5 0.75 0.9 1.0 1.1 1.25 2.0; do
        for run in `seq 1 20`; do
          timeout -k 5s -s TERM 70s env PYTHONPATH="$(realpath ./picn)" \
                  python3.6 picn-routing-measurements.py $timestamp $case $run \
                      $routing_interval $hopping_interval $(bc <<<"$hopping_interval*$lease_time") \
              || echo Timeout
        done
      done
    done
  done
done

python3.6 plot.py $timestamp
