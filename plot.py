
from typing import Dict, List

from matplotlib import pyplot as plt


def boxplot(data: Dict[int, List[float]]):
    ns = data.keys()
    values = data.values()
    plt.boxplot(values, labels=ns)
    plt.show()


def parse_csv(filename: str) -> Dict[int, List[float]]:
    with open(filename, 'r') as f:
        raw = f.read()
    lines = [l for l in raw.split('\n') if len(l) > 0]
    data: Dict[int, List[float]] = dict()
    for l in lines:
        n, _, t, ok = l.split(',')
        if ok != 'ok':
            continue
        n = int(n)
        t = float(t)
        if n not in data:
            data[n] = []
        data[n].append(t)
    return data


def plot_depth():
    boxplot(parse_csv('raw/depth.csv'))


def plot_breadth():
    boxplot(parse_csv('raw/breadth.csv'))


if __name__ == '__main__':
    plot_depth()
    plot_breadth()
