#!/usr/bin/env python3

import pandas as pd
import numpy as np
import wtfutil
import time
import pathlib
import datetime
import functools
import math
import json

FEEAGG_BUCKETS=800
MVS=1
PATH_PREFIX=(datetime.datetime.utcnow()-datetime.timedelta(0)).strftime('data/%Y/%m/%d/') 


dateref = datetime.datetime.utcnow()



pqdict_delta_24 = wtfutil.pqload_lastn_date(dateref, 'diff', 5760)
txpool_delta_24 = pd.concat(pqdict_delta_24).query('diff == 1')
feeagg_delta_24 = wtfutil.feeagg(txpool_delta_24, FEEAGG_BUCKETS) * 40 / len(pqdict_delta_24)


#PATH_PREFIX=datetime.datetime.utcnow().strftime('data/2017/12/26/') 
DELTA_DATAPOINTS=30 * 60 / 15 # 40 dp * 15 sec/dp = 600

COLORS=['#8cff66', '#ff668c', '#668cff']

# load the last DELTA_DATAPOINTS deltas
txpool_delta = pd.concat(wtfutil.pqload_lastn_date(dateref, 'diff', DELTA_DATAPOINTS)).query('diff == 1')
feeagg_delta = wtfutil.feeagg(txpool_delta, FEEAGG_BUCKETS) * 40 / DELTA_DATAPOINTS

txpool_mpool = pd.concat(wtfutil.pqload_lastn_date(dateref, 'full', 1).values())
feeagg_mpool = wtfutil.feeagg(txpool_mpool, FEEAGG_BUCKETS)

fn = functools.partial(wtfutil.cellfn_simulate, fa_start=feeagg_mpool, fa_delta=feeagg_delta, mvs=1.0)
df_simulation_large = wtfutil.df_simulation_large2

fa_demo = feeagg_mpool + feeagg_delta/2 # more exact since realtime
fn = functools.partial(wtfutil.cellfn_simulate, fa_start=fa_demo, fa_delta=feeagg_delta, mvs=1.0)
r=wtfutil.mp_map_df(fn, df_simulation_large)

fn_paid = functools.partial(
    wtfutil.cellfn_simulate, 
    fa_start=fa_demo, 
    fa_delta=feeagg_delta, 
    mvs=MVS,
)

fn_paid_24 = functools.partial(
    wtfutil.cellfn_simulate, 
    fa_start=fa_demo, 
    fa_delta=feeagg_delta_24, 
    mvs=MVS,
)

r_paid = wtfutil.mp_map_df(fn_paid, df_simulation_large)
r_paid_24 = wtfutil.mp_map_df(fn_paid_24, df_simulation_large)

se_mult = 1-(1 - np.array(r_paid.index)/144)**2
r_a = r_paid_24.multiply(se_mult, axis='index')
r_b = r_paid.multiply(1-se_mult, axis='index')

r = ((r_a+r_b))\
        .applymap(lambda x: int(np.ceil(x/20)*20))

data = json.dumps(r.to_dict('split')).replace('NaN', 'null')
with open('mvp/build/data.json', 'w') as f:
    f.write(data)
#print(data)

