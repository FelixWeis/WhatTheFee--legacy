#!/usr/bin/env python3
import os
import json
import pandas as pd
import numpy as np
import math
#import matplotlib.pyplot as plt
import time
import datetime

from operator import itemgetter
from pathlib import Path

from jsonrpc_requests import Server


import time

class Timer:
    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start


RPC_ENDPOINT = os.environ.get('RPC_ENDPOINT', 'http://user:pass@127.0.0.1:8332/')
FOLDER_PREFIX = os.environ.get('FOLDER_PREFIX', 'data')

bitcoind = Server(RPC_ENDPOINT)

prev_time_int = 0
prev_height = 0
prev_mempool_clean = {}

def rawmempool_cleanup(rmp):
    retval = dict()
    for k, v in rmp.items():
        #print(v['fees'])
        retval[k] = {
            'vsize': v['vsize'],
            'height': v['height'],
            'time': v['time'],
            'satoshi': int(v['fees']['base'] * 1e8),
            'is_woven': v['descendantcount'] != 1 or v['ancestorcount'] != 1
        }
    return retval

bitcoind.getblockchaininfo()

def isonow():
    return datetime.datetime.utcfromtimestamp(time.time()).isoformat()

print(
    isonow(),
    "Starting..."
    )
while True:
    time_int = int(time.time())
    if time_int % 15 != 0 or prev_time_int == time_int:
        time.sleep(0.01)
        continue
    else:
        folder = FOLDER_PREFIX + '/' + datetime.datetime.utcnow().strftime('%Y/%m/%d')
        prev_time_int = time_int

    print(
        isonow(),
        "Collecting..."
        )

    # call all
    with Timer() as t_getblockchaininfo_0:
        gbci0 = bitcoind.getblockchaininfo()
    with Timer() as t_getrawmempool:
        curr_mempool_raw = bitcoind.getrawmempool(True)
    #with Timer() as t_getrawmempool:
    # TODO: getblocktemplate
    #    curr_mempool_raw = bitcoind.getrawmempool(True)

    with Timer() as t_getblockchaininfo_1:
        gbci1 = bitcoind.getblockchaininfo()

    # height changed in current round? -> ignore
    if(gbci0['blocks'] != gbci1['blocks']):
        print(
            time_int,
            'height changed, ignoring round'
        )
        continue

    curr_height = gbci0['blocks']

    # cleanup
    with Timer() as t_rawmempool_cleanup:
        curr_mempool_clean = rawmempool_cleanup(curr_mempool_raw)


    curr_mempool_df = pd.DataFrame.from_dict(curr_mempool_clean, orient="index")

    # prepare a folder to store the data
    Path(folder).mkdir(parents=True, exist_ok=True)

    if prev_height == curr_height:
        idx_add = curr_mempool_df.index.difference(prev_mempool_df.index)
        idx_rem = prev_mempool_df.index.difference(curr_mempool_df.index)

        df_diff = pd.concat([
            prev_mempool_df.loc[idx_rem].assign(diff=-1),
            curr_mempool_df.loc[idx_add].assign(diff=1)
        ])

        filename = folder + f'/{curr_height}_{time_int}_diff.parq'
        df_diff.reset_index().to_parquet(filename)
        print(f'{curr_height} saved mempool DIFF ({len(idx_add)} add / {len(idx_rem)} rem)')

    else: # new blockheight: store full mempool

        filename = folder + f'/{curr_height}_{time_int}_full.parq'
        curr_mempool_df.reset_index().to_parquet(filename)
        print(f'{curr_height} saved FULL mempool')

    # storing curr to prev
    prev_mempool_df = curr_mempool_df
    prev_height = curr_height
    prev_time_int = time_int

    print(
        isonow(),
        datetime.datetime.utcfromtimestamp(time_int).strftime('%H:%M:%S'),
        'Requests timing',
        f'{t_getblockchaininfo_0.interval:.03f}',
        f"{t_getrawmempool.interval:.03f}",
        f'{t_getblockchaininfo_1.interval:.03f}'
        )



    #exit()

    #rawmempool_cleanup()



#filename = f'{curr_height}

# TODO: store 3rd delta: tx changing ancestor/descendant count
