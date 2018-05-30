
from typing import List, Tuple, Dict

import multiprocessing
import threading
import sys
import os
import queue
import random
from datetime import datetime, timedelta
from time import sleep

from PiCN.LayerStack import LayerStack
from PiCN.Layers.PacketEncodingLayer import BasicPacketEncodingLayer
from PiCN.Layers.ChunkLayer import BasicChunkLayer
from PiCN.Layers.LinkLayer import UDP4LinkLayer
from PiCN.Layers.PacketEncodingLayer.Encoder import NdnTlvEncoder
from PiCN.Layers.RoutingLayer.RoutingInformationBase import BaseRoutingInformationBase, TreeRoutingInformationBase
from PiCN.Layers.ICNLayer.ForwardingInformationBase import BaseForwardingInformationBase
from PiCN.Layers.RepositoryLayer.Repository import SimpleMemoryRepository
from PiCN.Packets import Name, Interest, Content
from PiCN.Processes import LayerProcess
from PiCN.ProgramLibs.ICNForwarder import ICNForwarder
from PiCN.ProgramLibs.ICNDataRepository import ICNDataRepository
from PiCN.ProgramLibs.Fetch import Fetch


now = ''
repo: ICNDataRepository = None
edge_index = -1
lock = threading.Lock()
running = True


def measure(fetch: Fetch, repo, forwarders, timeout: float, random_startup_delay: bool) -> Tuple[float, str]:
    repo.start_repo()
    if random_startup_delay:
        random.shuffle(forwarders)
    for f in forwarders:
        if random_startup_delay:
            sleep(random.uniform(0.1, 0.5))
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


def measure_depth_scaling(n: int, ageing: float, random_startup_delay: bool) -> Tuple[int, float, float, bool]:
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

    time, data = measure(fetch, repo, forwarders, n*ageing*3, random_startup_delay)
    return n, ageing, time, data == 'testcontent'


def depth_measurements(n: int, ageing: float, run: int, random_startup_delay: bool = False):
    testname = f'depth{"_rand" if random_startup_delay else ""}'
    measurements: List[Tuple[int, float, float, bool]] = []
    print(f'{testname} n={n}, ageing interval={ageing}, run {run}')
    measurements.append(measure_depth_scaling(n, ageing, random_startup_delay))
    os.makedirs('raw', exist_ok=True)
    filename = f'raw/{now}_{testname}.csv'
    with open(filename, 'a') as f:
        for i, a, t, ok in measurements:
            f.write(f'{i},{a},{t},{"ok" if ok else "fail"}\n')
    print(f'Wrote data to file {filename}')


def measure_breadth_scaling(n: int, ageing: float, random_startup_delay: bool) -> Tuple[int, float, float, bool]:
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

    time, data = measure(fetch, repo, forwarders, n*ageing*3, random_startup_delay)
    return n, ageing, time, data == 'testcontent'


def breadth_measurements(n: int, ageing: float, run: int, random_startup_delay: bool = False):
    testname = f'breadth{"_rand" if random_startup_delay else ""}'
    measurements: List[Tuple[int, float, float, bool]] = []
    print(f'{testname} n={n}, ageing interval={ageing}, run {run}')
    measurements.append(measure_breadth_scaling(n, ageing, random_startup_delay))
    os.makedirs('raw', exist_ok=True)
    filename = f'raw/{now}_{testname}.csv'
    with open(filename, 'a') as f:
        for i, a, t, ok in measurements:
            f.write(f'{i},{a},{t},{"ok" if ok else "fail"}\n')
    print(f'Wrote data to file {filename}')


def measure_repo_hopping(routing_interval: float, hopping_interval: float, lease_time: float, edge_traverse: bool)\
        -> Tuple[float, float, float]:
    global repo, lock, running
    manager = multiprocessing.Manager()
    autoconfig_edgeprefix: List[Tuple[Name, bool]] = [(Name('/edge'), False)]
    nodes: Dict[int, ICNForwarder] = dict()
    ports: Dict[int, Tuple[str, int]] = dict()
    edgeports: List[int] = list()

    # Initialize core nodes
    for c in [00, 10, 20, 30]:
        nodes[c] = ICNForwarder(9000 + c, encoder=NdnTlvEncoder(), routing=True, peers=[])
        ports[c] = nodes[c].linklayer.sock.getsockname()
    # Initialize edge nodes
    for e in [11, 12, 13, 21, 22, 23, 31, 32, 33]:
        nodes[e] = ICNForwarder(9000 + e, encoder=NdnTlvEncoder(), routing=True, peers=[], autoconfig=True)
        ports[e] = nodes[e].linklayer.sock.getsockname()
        edgeports.append(ports[e][1])

    # Assign routing peers after the OS assigned UDP ports. Each node knows the nodes one layer "beneath" itself
    # in above graph as its routing peers.
    nodes[00].routinglayer._peers = [ports[10], ports[20], ports[30]]
    nodes[10].routinglayer._peers = [ports[11], ports[12], ports[13]]
    nodes[20].routinglayer._peers = [ports[21], ports[22], ports[23]]
    nodes[30].routinglayer._peers = [ports[31], ports[32], ports[33]]

    # Set up faces and static FIB of core00 node.
    fid00to10: int = nodes[00].linklayer.get_or_create_fid(ports[10], static=True)
    fid00to20: int = nodes[00].linklayer.get_or_create_fid(ports[20], static=True)
    fid00to30: int = nodes[00].linklayer.get_or_create_fid(ports[30], static=True)
    fib00: BaseForwardingInformationBase = nodes[00].data_structs['fib']
    if edge_traverse:
        fib00.add_fib_entry(Name('/edge'), fid00to10, static=True)
        fib00.add_fib_entry(Name('/edge'), fid00to20, static=True)
        fib00.add_fib_entry(Name('/edge'), fid00to30, static=True)
    nodes[00].data_structs['fib'] = fib00
    nodes[00].data_structs['rib'] = TreeRoutingInformationBase(manager, shortest_only=False)

    # Set up faces and static FIB of core10 node.
    fid10to11: int = nodes[10].linklayer.get_or_create_fid(ports[11], static=True)
    fid10to12: int = nodes[10].linklayer.get_or_create_fid(ports[12], static=True)
    fid10to13: int = nodes[10].linklayer.get_or_create_fid(ports[13], static=True)
    fib10: BaseForwardingInformationBase = nodes[10].data_structs['fib']
    if edge_traverse:
        fib10.add_fib_entry(Name('/edge'), fid10to11, static=True)
        fib10.add_fib_entry(Name('/edge'), fid10to12, static=True)
        fib10.add_fib_entry(Name('/edge'), fid10to13, static=True)
    nodes[10].data_structs['fib'] = fib10
    nodes[10].data_structs['rib'] = TreeRoutingInformationBase(manager, shortest_only=False)

    # Set up faces and static FIB of core20 node.
    fid20to21: int = nodes[20].linklayer.get_or_create_fid(ports[21], static=True)
    fid20to22: int = nodes[20].linklayer.get_or_create_fid(ports[22], static=True)
    fid20to23: int = nodes[20].linklayer.get_or_create_fid(ports[23], static=True)
    fib20: BaseForwardingInformationBase = nodes[20].data_structs['fib']
    if edge_traverse:
        fib20.add_fib_entry(Name('/edge'), fid20to21, static=True)
        fib20.add_fib_entry(Name('/edge'), fid20to22, static=True)
        fib20.add_fib_entry(Name('/edge'), fid20to23, static=True)
    nodes[20].data_structs['fib'] = fib20
    nodes[20].data_structs['rib'] = TreeRoutingInformationBase(manager, shortest_only=False)

    # Set up faces and static FIB of core30 node.
    fid30to31: int = nodes[30].linklayer.get_or_create_fid(ports[31], static=True)
    fid30to32: int = nodes[30].linklayer.get_or_create_fid(ports[32], static=True)
    fid30to33: int = nodes[30].linklayer.get_or_create_fid(ports[33], static=True)
    fib30: BaseForwardingInformationBase = nodes[30].data_structs['fib']
    if edge_traverse:
        fib30.add_fib_entry(Name('/edge'), fid30to31, static=True)
        fib30.add_fib_entry(Name('/edge'), fid30to32, static=True)
        fib30.add_fib_entry(Name('/edge'), fid30to33, static=True)
    nodes[30].data_structs['fib'] = fib30
    nodes[30].data_structs['rib'] = TreeRoutingInformationBase(manager, shortest_only=False)

    for node in [00, 10, 20, 30]:
        nodes[node].routinglayer._ageing_interval = routing_interval

    # Set up network edge autoconfig.
    for e in [11, 12, 13, 21, 22, 23, 31, 32, 33]:
        nodes[e].autoconfiglayer._service_registration_prefixes = autoconfig_edgeprefix
        nodes[e].routinglayer._ageing_interval = routing_interval
        nodes[e].autoconfiglayer._service_registration_timeout = timedelta(seconds=lease_time)

    forwarders = list(nodes.values())
    random.shuffle(forwarders)
    for n in forwarders:
        n.start_forwarder()
        sleep(0.05)

    imr = SimpleMemoryRepository(Name('/edge/hoppingrepo'), manager)
    n = 600
    for i in range(n):
        imr.add_content(Name(f'/edge/hoppingrepo/{i}'), f'content {i}')

    def repo_hop():
        global repo, edge_index, lock, running
        if repo is not None:
            repo.stop_repo()
        with lock:
            if not running:
                return
        repo = ICNDataRepository(None, Name('/hoppingrepo'), 0, encoder=NdnTlvEncoder(),
                                 autoconfig=True, autoconfig_routed=True)
        repo.repolayer._repository = imr
        edge_index = (edge_index + 1) % len(edgeports)
        repo.autoconfiglayer._broadcast_port = edgeports[edge_index]
        repo.start_repo()
        threading.Timer(hopping_interval, repo_hop).start()

    repo_hop()

    class DurationTaggingLayer(LayerProcess):

        def __init__(self):
            super().__init__('DurationTaggingLayer')
            self._names: Dict[Name, datetime] = dict()

        def data_from_lower(self, to_lower: multiprocessing.Queue, to_higher: multiprocessing.Queue, data):
            fid, packet = data
            if packet.name in self._names:
                to_higher.put([fid, packet, (datetime.utcnow() - self._names[packet.name]).total_seconds()])
                del self._names[packet.name]
            else:
                to_higher.put([fid, packet, None])

        def data_from_higher(self, to_lower: multiprocessing.Queue, to_higher: multiprocessing.Queue, data):
            fid, packet = data
            self._names[packet.name] = datetime.utcnow()
            to_lower.put(data)

    linklayer = UDP4LinkLayer(port=0)
    fetch_fid = linklayer.create_new_fid(ports[00], True)
    fetch = LayerStack([
        DurationTaggingLayer(),
        BasicChunkLayer(),
        BasicPacketEncodingLayer(NdnTlvEncoder()),
        linklayer
    ])
    end_time = datetime.utcnow()
    fetch.start_all()
    for i in range(n):
        fetch.queue_from_higher.put([fetch_fid, Interest(Name(f'/edge/hoppingrepo/{i}'))])
        end_time += timedelta(milliseconds=100)
        delay = (end_time - datetime.utcnow()).total_seconds()
        if delay > 0:
            sleep(delay)
    satisfied_interests: Dict[int, bool] = dict()
    satisfied_interests_outoforder: Dict[int, bool] = dict()
    maxreceived = -1
    avgduration = 0
    while not fetch.queue_to_higher.empty():
        _, data, duration = fetch.queue_to_higher.get()
        if isinstance(data, Content) and data.content.startswith('content '):
            _, i = data.content.split(' ', 1)
            i = int(i)
            satisfied_interests_outoforder[i] = True
            avgduration += duration
            if i <= maxreceived:
                continue
            maxreceived = i
            satisfied_interests[i] = True
    success = len(satisfied_interests)
    success_outoforder = len(satisfied_interests_outoforder)
    fetch.stop_all()
    for f in nodes.values():
        f.stop_forwarder()
    if repo is not None:
        repo.stop_repo()
    with lock:
        running = False
    return success / n, success_outoforder / n, avgduration / success if success > 0 else 0.0


def repo_hopping_measurements(run: int, routing_interval: float, hopping_interval: float, lease_time: float,
                              edge_traverse: bool = False):
    testname = f'repo_hopping{"_edge_traverse" if edge_traverse else ""}'
    measurements: List[Tuple[float, float, float]] = []
    print(f'{testname} routing interval={routing_interval}, hopping interval={hopping_interval}, lease time=' +
          f'{lease_time}, run {run}')
    measurements.append(measure_repo_hopping(routing_interval, hopping_interval, lease_time, edge_traverse))
    os.makedirs('raw', exist_ok=True)
    filename = f'raw/{now}_{testname}.csv'
    with open(filename, 'a') as f:
        for success, succes_outoforder, avg in measurements:
            f.write(f'{routing_interval},{hopping_interval},{lease_time},{success},{succes_outoforder},{avg}\n')
    print(f'Wrote data to file {filename}')


def main():
    global now
    if len(sys.argv) < 4:
        print(f'Usage: {sys.argv[0]} <timestamp> <case> <run> [param1] ... [paramN]')
        exit(1)
    now = sys.argv[1]
    case = sys.argv[2]
    run = int(sys.argv[3])
    if case == 'depth':
        if len(sys.argv) < 6:
            print(f'Usage: {sys.argv[0]} {now} {case} {run} <n> <interval>')
            exit(1)
        n = int(sys.argv[4])
        ageing_interval = float(sys.argv[5])
        depth_measurements(n, ageing_interval, run)
    elif case == 'breadth':
        if len(sys.argv) < 6:
            print(f'Usage: {sys.argv[0]} {now} {case} {run} <n> <interval>')
            exit(1)
        n = int(sys.argv[4])
        ageing_interval = float(sys.argv[5])
        breadth_measurements(n, ageing_interval, run)
    elif case == 'depth_rand':
        if len(sys.argv) < 6:
            print(f'Usage: {sys.argv[0]} {now} {case} {run} <n> <interval>')
            exit(1)
        n = int(sys.argv[4])
        ageing_interval = float(sys.argv[5])
        depth_measurements(n, ageing_interval, run, random_startup_delay=True)
    elif case == 'breadth_rand':
        if len(sys.argv) < 6:
            print(f'Usage: {sys.argv[0]} {now} {case} {run} <n> <interval>')
            exit(1)
        n = int(sys.argv[4])
        ageing_interval = float(sys.argv[5])
        breadth_measurements(n, ageing_interval, run, random_startup_delay=True)
    elif case == 'repo_hopping':
        if len(sys.argv) < 7:
            print(f'Usage: {sys.argv[0]} {now} {case} {run} <routing_interval> <hopping_interval> <lease_time>')
            exit(1)
        routing_interval = float(sys.argv[4])
        hopping_interval = float(sys.argv[5])
        lease_time = float(sys.argv[6])
        repo_hopping_measurements(run, routing_interval, hopping_interval, lease_time)
    elif case == 'repo_hopping_edge_traverse':
        if len(sys.argv) < 7:
            print(f'Usage: {sys.argv[0]} {now} {case} {run} <routing_interval> <hopping_interval> <lease_time>')
            exit(1)
        routing_interval = float(sys.argv[4])
        hopping_interval = float(sys.argv[5])
        lease_time = float(sys.argv[6])
        repo_hopping_measurements(run, routing_interval, hopping_interval, lease_time, edge_traverse=True)


if __name__ == '__main__':
    main()
