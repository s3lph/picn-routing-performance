
from typing import Dict, List, Tuple

import sys
import os

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.lines


def scaling_boxplot(data: Dict[str, Dict[int, List[float]]], basename, ymax: float):
    intervals = data.keys()
    for interval in intervals:
        ns = data[interval].keys()
        values = data[interval].values()
        plt.figure()
        plt.boxplot(values,
                    labels=ns,
                    sym='+r',
                    whis=[5, 95],
                    medianprops=dict(linestyle='-', color='black'))
        plt.xlabel('nodes')
        plt.ylabel('time [s]')
        plt.ylim(ymin=0, ymax=ymax * 1.1)
        plt.title(f'interval = {interval}')
        plt.savefig(basename.format(t=now, i=interval))
        plt.close()


def parse_scaling_csv(filename: str) -> Dict[str, Dict[int, List[float]]]:
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


def plot_scaling():
    depth_data = parse_scaling_csv(f'raw/{now}_depth.csv')
    depth_rand_data = parse_scaling_csv(f'raw/{now}_depth_rand.csv')
    depth_ymax = max(max([v for n in depth_data.values() for i in n.values() for v in i]),
                     max([v for n in depth_rand_data.values() for i in n.values() for v in i]))
    scaling_boxplot(depth_data, 'plots/{t}_depth_{i}.png', depth_ymax)
    scaling_boxplot(depth_rand_data, 'plots/{t}_depth_rand_{i}.png', depth_ymax)

    breadth_data = parse_scaling_csv(f'raw/{now}_breadth.csv')
    breadth_rand_data = parse_scaling_csv(f'raw/{now}_breadth_rand.csv')
    breadth_ymax = max(max([v for n in breadth_data.values() for i in n.values() for v in i]),
                       max([v for n in breadth_rand_data.values() for i in n.values() for v in i]))
    scaling_boxplot(breadth_data, 'plots/{t}_breadth_{i}.png', breadth_ymax)
    scaling_boxplot(breadth_rand_data, 'plots/{t}_breadth_rand_{i}.png', breadth_ymax)


def parse_hopping_csv(filename: str):
    with open(filename, 'r') as f:
        raw = f.read()
    lines = [l for l in raw.split('\n') if len(l) > 0]
    data: Dict[Tuple[str, str, str], Tuple[List[float], List[float], List[float]]] = dict()
    for l in lines:
        routing_interval, hopping_interval, lease_time, success, success_ooo, avgduration = l.split(',')
        success = float(success)
        success_ooo = float(success_ooo)
        avgduration = float(avgduration)
        key = (routing_interval, hopping_interval, lease_time)
        if key not in data:
            data[key] = list(), list(), list()
        data[key][0].append(success)
        data[key][1].append(success_ooo)
        data[key][2].append(avgduration)
    return data


def mkcolor(val: float, low: str, high: str) -> str:
    result = '#'
    for comp in [1, 3, 5]:
        l = int(low[comp:comp+2], base=16)
        h = int(high[comp:comp+2], base=16)
        r = int(h * val + l * (1 - val))
        result += '{0:02x}'.format(r)
    return result


def hopping_plot_single_vars(data: Dict[Tuple[str, str, str], Tuple[List[float], List[float], List[float]]],
                             basename: str):
    routing_intervals = sorted(list(set([k[0] for k in data.keys()])), key=lambda x: float(x))
    hopping_intervals = sorted(list(set([k[1] for k in data.keys()])), key=lambda x: float(x))
    lease_timeouts = sorted(list(set([k[2] for k in data.keys()])), key=lambda x: float(x))

    rsvals = list()
    rdvals = list()
    for routing_interval in routing_intervals:
        keys = [k for k in data.keys() if k[0] == routing_interval]
        rsvals.append([x for k in keys for x in data[k][0]])
        rdvals.append([x for k in keys for x in data[k][2]])

    hsvals = list()
    hdvals = list()
    for hopping_interval in hopping_intervals:
        keys = [k for k in data.keys() if k[1] == hopping_interval]
        hsvals.append([x for k in keys for x in data[k][0]])
        hdvals.append([x for k in keys for x in data[k][2]])

    lsvals = list()
    ldvals = list()
    for lease_timeout in lease_timeouts:
        keys = [k for k in data.keys() if k[2] == lease_timeout]
        lsvals.append([x for k in keys for x in data[k][0]])
        ldvals.append([x for k in keys for x in data[k][2]])

    duration_ymax: float = max(max(max(rdvals)), max(max(hdvals)), max(max(ldvals)))

    plt.figure()
    plt.boxplot(rsvals,
                positions=[float(x) for x in routing_intervals],
                labels=routing_intervals,
                sym='+r',
                whis=[5, 95],
                medianprops=dict(linestyle='-', color='black'))
    plt.xlabel('routing interval [s]')
    plt.ylabel('success rate')
    plt.ylim(ymin=0, ymax=1.1)
    plt.savefig(basename.format(t=now, r='success', var='r'))
    plt.close()

    plt.figure()
    plt.boxplot(hsvals,
                positions=[float(x) for x in hopping_intervals],
                labels=hopping_intervals,
                sym='+r',
                whis=[5, 95],
                medianprops=dict(linestyle='-', color='black'))
    plt.xlabel('hopping interval [s]')
    plt.ylabel('success rate')
    plt.ylim(ymin=0, ymax=1.1)
    plt.savefig(basename.format(t=now, r='success', var='h'))
    plt.close()

    plt.figure()
    plt.boxplot(lsvals,
                positions=[float(x) for x in lease_timeouts],
                labels=['' if x in ['4.5', '5.5', '9.0', '11.0', '18.0', '22.0'] else x for x in lease_timeouts],
                sym='+r',
                whis=[5, 95],
                medianprops=dict(linestyle='-', color='black'))
    plt.xlabel('lease timeout [s]')
    plt.ylabel('success rate')
    plt.ylim(ymin=0, ymax=1.1)
    plt.savefig(basename.format(t=now, r='success', var='l'))
    plt.close()

    plt.figure()
    plt.boxplot(rdvals,
                positions=[float(x) for x in routing_intervals],
                labels=routing_intervals,
                sym='+r',
                whis=[5, 95],
                medianprops=dict(linestyle='-', color='black'))
    plt.xlabel('routing interval [s]')
    plt.ylabel('average duration [s]')
    plt.ylim(ymin=0, ymax=duration_ymax)
    plt.savefig(basename.format(t=now, r='duration', var='r'))
    plt.close()

    plt.figure()
    plt.boxplot(hdvals,
                positions=[float(x) for x in hopping_intervals],
                labels=hopping_intervals,
                sym='+r',
                whis=[5, 95],
                medianprops=dict(linestyle='-', color='black'))
    plt.xlabel('hopping interval [s]')
    plt.ylabel('average duration [s]')
    plt.ylim(ymin=0, ymax=duration_ymax)
    plt.savefig(basename.format(t=now, r='duration', var='h'))
    plt.close()

    plt.figure()
    plt.boxplot(ldvals,
                positions=[float(x) for x in lease_timeouts],
                labels=['' if x in ['4.5', '5.5', '9.0', '11.0', '18.0', '22.0'] else x for x in lease_timeouts],
                sym='+r',
                whis=[5, 95],
                medianprops=dict(linestyle='-', color='black'))
    plt.xlabel('lease timeout [s]')
    plt.ylabel('average duration [s]')
    plt.ylim(ymin=0, ymax=duration_ymax)
    plt.savefig(basename.format(t=now, r='duration', var='l'))
    plt.close()


def hopping_plot_success_rate_l_vs_h(data: Dict[Tuple[str, str, str], Tuple[List[float], List[float], List[float]]],
                                     basename: str):
    scale = 750
    lowcolor = '#000000'
    highcolor = '#ff0000'
    routing_intervals = set(k[0] for k in data.keys())
    for routing_interval in routing_intervals:
        keys = [k for k in data.keys() if k[0] == routing_interval]
        x = list()
        y = list()
        avg = list()
        c = list()
        smin = 1.0
        smax = 0.0
        mean = 0.0
        for k in keys:
            s, sooo, duration = data[k]
            val = sum(s)/len(s)
            smin = min(smin, val)
            smax = max(smax, val)
            mean += val
            x.append([float(k[2])])
            y.append([float(k[1])])
            avg.append((val**2) * scale)
            c.append(mkcolor(val, lowcolor, highcolor))
        mean /= len(avg)
        plt.figure()
        plt.scatter(x, y, s=avg, c=c)
        plt.ylim([0, 22])
        # Legend proxies
        mean_proxy = matplotlib.lines.Line2D([], [],
                                             label='{:.1f}% (mean)'.format(mean * 100),
                                             linewidth=0,
                                             marker='.',
                                             markeredgecolor='k',
                                             markeredgewidth=.5,
                                             markerfacecolor=mkcolor(mean, lowcolor, highcolor),
                                             markersize=20)
        lower_bound = matplotlib.lines.Line2D([], [],
                                              label='{:.1f}% (min)'.format(smin * 100),
                                              linewidth=0,
                                              marker='.',
                                              markeredgecolor='k',
                                              markeredgewidth=.5,
                                              markerfacecolor=mkcolor(smin, lowcolor, highcolor),
                                              markersize=20)
        upper_bound = matplotlib.lines.Line2D([], [],
                                              label='{:.1f}% (max)'.format(smax * 100),
                                              linewidth=0,
                                              marker='.',
                                              markeredgecolor='k',
                                              markeredgewidth=.5,
                                              markerfacecolor=mkcolor(smax, lowcolor, highcolor),
                                              markersize=20)
        plt.legend(title='Success rates',
                   handles=[upper_bound, mean_proxy, lower_bound])
        plt.xlabel('prefix lease time [s]')
        plt.ylabel('hopping interval [s]')
        plt.title(f'routing interval = {routing_interval}s')
        plt.savefig(basename.format(t=now, i=routing_interval))
        plt.close()


def hopping_plot_success_rate_l_vs_r(data: Dict[Tuple[str, str, str], Tuple[List[float], List[float], List[float]]],
                                     basename: str):
    scale = 750
    lowcolor = '#000000'
    highcolor = '#ff0000'
    hopping_intervals = set(k[1] for k in data.keys())
    for hopping_interval in hopping_intervals:
        keys = [k for k in data.keys() if k[1] == hopping_interval]
        x = list()
        y = list()
        savg = list()
        sc = list()
        smin = 1.0
        smax = 0.0
        smean = 0.0
        for k in keys:
            s, sooo, duration = data[k]
            sval = sum(s)/len(s)
            smin = min(smin, sval)
            smax = max(smax, sval)
            smean += sval
            x.append([float(k[2])])
            y.append([float(k[0])])
            savg.append((sval**2) * scale)
            sc.append(mkcolor(sval, lowcolor, highcolor))
        smean /= len(savg)

        plt.figure()
        plt.scatter(x, y, s=savg, c=sc)
        plt.ylim([0, 2.5])
        # Legend proxies
        upper_bound = matplotlib.lines.Line2D([], [],
                                              label='{:.1f}% (max)'.format(smax * 100),
                                              linewidth=0,
                                              marker='.',
                                              markeredgecolor='k',
                                              markeredgewidth=.5,
                                              markerfacecolor=mkcolor(smax, lowcolor, highcolor),
                                              markersize=20)
        mean_proxy = matplotlib.lines.Line2D([], [],
                                             label='{:.1f}% (mean)'.format(smean * 100),
                                             linewidth=0,
                                             marker='.',
                                             markeredgecolor='k',
                                             markeredgewidth=.5,
                                             markerfacecolor=mkcolor(smean, lowcolor, highcolor),
                                             markersize=20)
        lower_bound = matplotlib.lines.Line2D([], [],
                                              label='{:.1f}% (min)'.format(smin * 100),
                                              linewidth=0,
                                              marker='.',
                                              markeredgecolor='k',
                                              markeredgewidth=.5,
                                              markerfacecolor=mkcolor(smin, lowcolor, highcolor),
                                              markersize=20)
        plt.legend(title='Success rates',
                   handles=[upper_bound, mean_proxy, lower_bound],
                   loc='lower right',
                   bbox_to_anchor=(0.9, 0.0))
        plt.xlabel('prefix lease time [s]')
        plt.ylabel('routing interval [s]')
        plt.title(f'hopping interval = {hopping_interval}s')
        plt.savefig(basename.format(r='success', t=now, i=hopping_interval))
        plt.close()


def plot_hopping():
    data = parse_hopping_csv(f'raw/{now}_repo_hopping.csv')
    hopping_plot_single_vars(data, 'plots/{t}_repo_hopping_{r}_{var}.png')
    hopping_plot_success_rate_l_vs_h(data, 'plots/{t}_repo_hopping_success_l_vs_h_{i}.png')
    hopping_plot_success_rate_l_vs_r(data, 'plots/{t}_repo_hopping_{r}_l_vs_r_{i}.png')

    data_et = parse_hopping_csv(f'raw/{now}_repo_hopping_edge_traverse.csv')
    hopping_plot_single_vars(data_et, 'plots/{t}_repo_hopping_edge_traverse_{r}_{var}.png')
    hopping_plot_success_rate_l_vs_h(data_et, 'plots/{t}_repo_hopping_edge_traverse_success_l_vs_h_{i}.png')
    hopping_plot_success_rate_l_vs_r(data_et, 'plots/{t}_repo_hopping_edge_traverse_{r}_l_vs_r_{i}.png')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'{sys.argv[0]} <timestamp>')
        exit(1)
    now = sys.argv[1]
    os.makedirs('plots', exist_ok=True)
    plot_scaling()
    plot_hopping()
