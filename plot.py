
from typing import Dict, List

import sys
import os

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt


def boxplot(data: Dict[str, Dict[int, List[float]]], basename):
    intervals = data.keys()
    ymax = max([v for n in data.values() for i in n.values() for v in i])
    for interval in intervals:
        ns = data[interval].keys()
        values = data[interval].values()
        plt.figure()
        plt.boxplot(values, labels=ns, sym='+r', medianprops=dict(linestyle='-', color='black'))
        plt.xlabel('nodes')
        plt.ylabel('time [s]')
        plt.ylim(ymin=0, ymax=ymax * 1.1)
        plt.title(f'interval = {interval}')
        plt.savefig(basename.format(t=now, i=interval))
        plt.close()


def parse_csv(filename: str) -> Dict[str, Dict[int, List[float]]]:
    with open(filename, 'r') as f:
        raw = f.read()
    lines = [l for l in raw.split('\n') if len(l) > 0]
    data: Dict[str, Dict[int, List[float]]] = dict()
    for l in lines:
        n, interval, t, ok = l.split(',')
        if ok != 'ok':
            continue
        n = int(n)
        t = float(t)
        if interval not in data:
            data[interval] = dict()
        if n not in data[interval]:
            data[interval][n] = list()
        data[interval][n].append(t)
    return data


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'{sys.argv[0]} <timestamp>')
        exit(1)
    now = sys.argv[1]
    os.makedirs('plots', exist_ok=True)
    boxplot(parse_csv(f'raw/{now}_depth.csv'), 'plots/{t}_depth_{i}.png')
    boxplot(parse_csv(f'raw/{now}_breadth.csv'), 'plots/{t}_breadth_{i}.png')
    boxplot(parse_csv(f'raw/{now}_depth_rand.csv'), 'plots/{t}_depth_rand_{i}.png')
    boxplot(parse_csv(f'raw/{now}_breadth_rand.csv'), 'plots/{t}_breadth_rand_{i}.png')
