
from typing import List, Tuple

import sys
import os
import queue
from datetime import datetime, timedelta
from time import sleep

from PiCN.Layers.PacketEncodingLayer.Encoder import NdnTlvEncoder
from PiCN.Layers.RoutingLayer.RoutingInformationBase import BaseRoutingInformationBase
from PiCN.Packets import Name
from PiCN.ProgramLibs.ICNForwarder import ICNForwarder
from PiCN.ProgramLibs.ICNDataRepository import ICNDataRepository
from PiCN.ProgramLibs.Fetch import Fetch


def measure(fetch: Fetch, repo, forwarders, timeout: float) -> Tuple[float, str]:
    repo.start_repo()
    for f in forwarders:
        f.start_forwarder()
    data = ''
    start_time = datetime.utcnow()
    while datetime.utcnow() < start_time + timedelta(seconds=timeout):
        try:
            data = fetch.fetch_data(Name('/picn/routing/testrepo/testcontent'), 1.0)
            if data != 'testcontent':
                sleep(0.1)
                continue
            else:
                break
        except queue.Empty:
            pass
    end_time = datetime.utcnow()
    repo.stop_repo()
    for f in forwarders:
        f.stop_forwarder()
    fetch.stop_fetch()
    return (end_time - start_time).total_seconds(), data


def measure_depth_scaling(n: int, ageing: float) -> Tuple[int, float, float, bool]:
    forwarders: List[ICNForwarder] = []
    for i in range(n):
        forwarders.append(ICNForwarder(0, encoder=NdnTlvEncoder(), routing=True))
    repo = ICNDataRepository(None, Name('/picn/routing/testrepo'), port=0, encoder=NdnTlvEncoder())
    for i in range(n):
        if i < len(forwarders) - 1:
            forwarders[i].routinglayer._peers.append(forwarders[i+1].linklayer.sock.getsockname())
        if i == len(forwarders) - 1:
            fid = forwarders[i].linklayer.get_or_create_fid(repo.linklayer.sock.getsockname(), static=True)
            rib: BaseRoutingInformationBase = forwarders[i].data_structs['rib']
            rib.insert(Name('/picn/routing/testrepo'), fid, 1)
            forwarders[i].data_structs['rib'] = rib
        forwarders[i].routinglayer._ageing_interval = ageing
    repo.repo.add_content(Name('/picn/routing/testrepo/testcontent'), 'testcontent')
    fetchaddr = forwarders[0].linklayer.sock.getsockname()
    fetch = Fetch(fetchaddr[0], fetchaddr[1], encoder=NdnTlvEncoder())

    time, data = measure(fetch, repo, forwarders, timeout=n*ageing*3)
    return n, ageing, time, data == 'testcontent'


def depth_measurements(n: int, ageing: float, run: int):
    measurements: List[Tuple[int, float, float, bool]] = []
    print(f'n={n}, ageing interval={ageing}, run {run}')
    measurements.append(measure_depth_scaling(n, ageing))
    os.makedirs('raw', exist_ok=True)
    with open('raw/depth.csv', 'a') as f:
        for i, a, t, ok in measurements:
            f.write(f'{i},{a},{t},{"ok" if ok else "fail"}\n')
    print('Saved data to file raw/depth.csv')


def measure_breadth_scaling(n: int, ageing: float) -> Tuple[int, float, float, bool]:
    forwarders: List[ICNForwarder] = []
    for i in range(n):
        forwarders.append(ICNForwarder(0, encoder=NdnTlvEncoder(), routing=True))
    forwarders.append(ICNForwarder(0, encoder=NdnTlvEncoder(), routing=True))
    forwarders.append(ICNForwarder(0, encoder=NdnTlvEncoder(), routing=True))
    repo = ICNDataRepository(None, Name('/picn/routing/testrepo'), port=0, encoder=NdnTlvEncoder())
    for i in range(n):
        forwarders[i].routinglayer._peers.append(forwarders[-1].linklayer.sock.getsockname())
        forwarders[-2].routinglayer._peers.append(forwarders[i].linklayer.sock.getsockname())
    for f in forwarders:
        f.routinglayer._ageing_interval = ageing
    fid = forwarders[-1].linklayer.get_or_create_fid(repo.linklayer.sock.getsockname(), static=True)
    rib: BaseRoutingInformationBase = forwarders[-1].data_structs['rib']
    rib.insert(Name('/picn/routing/testrepo'), fid, 1)
    forwarders[-1].data_structs['rib'] = rib
    repo.repo.add_content(Name('/picn/routing/testrepo/testcontent'), 'testcontent')
    fetchaddr = forwarders[-2].linklayer.sock.getsockname()
    fetch = Fetch(fetchaddr[0], fetchaddr[1], encoder=NdnTlvEncoder())

    time, data = measure(fetch, repo, forwarders, timeout=n*3)
    return n, ageing, time, data == 'testcontent'


def breadth_measurements(n: int, ageing: float, run: int):
    measurements: List[Tuple[int, float, float, bool]] = []
    print(f'n={n}, ageing interval={ageing}, run {run}')
    measurements.append(measure_breadth_scaling(n, ageing))
    os.makedirs('raw', exist_ok=True)
    with open('raw/breadth.csv', 'a') as f:
        for i, a, t, ok in measurements:
            f.write(f'{i},{a},{t},{"ok" if ok else "fail"}\n')
    print('Saved data to file raw/breadth.csv')


def main():
    if len(sys.argv) < 4:
        print(f'Usage: {sys.argv[0]} <n> <run> <ageing_interval>')
        sys.exit(1)
    n = int(sys.argv[1])
    run = int(sys.argv[2])
    ageing_interval = float(sys.argv[3])
    depth_measurements(n, ageing_interval, run)
    breadth_measurements(n, ageing_interval, run)


if __name__ == '__main__':
    main()
