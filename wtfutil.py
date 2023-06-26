import numpy as np
import pandas as pd
import math
import pathlib
import pyarrow.parquet as pq
import time
import colorsys
import datetime


def feeagg(df_txpool, bcount=20, bmax=800):
    #assert(buckets in [10,20,25,40,50,100,125,200,250,500,1000])
    assert(bmax%bcount==0)
    factor = bmax//bcount
    df = df_txpool[['satoshi', 'vsize']]
    df = df.assign(
        cnt=1,
        feerate_lfb=np.minimum(np.round(np.log(
            df['satoshi']/df['vsize'] # aka feerate
        ) * 100 / factor) * factor, bmax).astype(int)
    )
    
    agg0 = df.groupby('feerate_lfb').sum()[['cnt', 'vsize', 'satoshi']]
    
    agg = pd.DataFrame()
    agg = agg.assign(
        cnt= agg0['cnt'],
        btc= agg0['satoshi'] / 1e8,
        mvs= agg0['vsize'] / 1e6,
    )

    idx = np.arange(bcount+1)*factor
    agg = agg.reindex(idx[::-1], fill_value=0.0)
    
    return agg


def mine_series(values, left=1.0):
    l = len(values)
    a, b, c = np.zeros(l), np.zeros(l), np.zeros(l)

    ilowest = -1
    for i, z in enumerate(values):
        na = min(z, left)
        left = left - na
        nb = z - na
        a[i] = na
        b[i] = nb
        c[i] = 0.0 if nb == 0 else nb/z
        if b[i] == 0.0 and i-1 == ilowest:
            ilowest = i
    return (a, b, c, ilowest)


def simulate_simple(vals_mempool, vals_delta, nmeans, nblocks, mvs=1.0, onlylast=False):
    steps = []
    if nblocks <= 0:
        return steps
    
    avg_timeframe = nmeans/nblocks
    vals_prev = vals_mempool.copy()
    
    for i in range(nblocks):
        vals_prev += vals_delta * avg_timeframe
        vals_mined, vals_post, vals_multiply, index_best = mine_series(vals_prev, mvs)
        if not onlylast:
            steps.append((vals_mined, vals_post, vals_multiply, index_best))
        vals_prev = vals_post
    if onlylast: # TODO: still used?
        return steps[-1]
    return steps



def cellfn_add(c, i, v, number=1.0):
    return (c, i, v+number)

def cellfn_simulate(c, i, v, fa_start, fa_delta, mvs, timeit=False):
    s = simulate_simple(
        vals_mempool=fa_start.mvs, 
        vals_delta=fa_delta.mvs,
        mvs=mvs,
        nmeans=i,
        nblocks=v,
        onlylast=False
    )
    if len(s):
        outv = fa_start.index[s[-1][-1]]
    else:
        outv = None
    return (c, i, outv)



def mp_map_df(fn, df):
    """
    Apply a function to each cell, 
    then reassemble the result into a dataframe with same columns/index
    """
    lst_in = []
    for c in df.columns:
        for i in df.index:
            v = df.loc[i, c]
            lst_in.append((c,i,v))

    # mock mp for now
    lst_out = [fn(c,i,v) for (c,i,v) in lst_in]
    
    d = dict()
    for (a,b,c) in lst_out:
        if not a in d:
            d[a] = dict()
        if not b in d[a]:
            d[a][b] = dict()
        d[a][b] = c
    
    return pd.DataFrame(d)




# generated using math-certatinty notebook
df_simulation_large = pd.DataFrame({
  '0.0995': {3: 5, 6: 9, 9: 13, 12: 17, 18: 24, 24: 30, 36: 44, 48: 57, 72: 83, 96: 109, 144: 159},
  '0.1974': {3: 4, 6: 8, 9: 11, 12: 15, 18: 22, 24: 28, 36: 41, 48: 54, 72: 79, 96: 104, 144: 154},
  '0.5000': {3: 3, 6: 6, 9: 9, 12: 12, 18: 18, 24: 24, 36: 36, 48: 48, 72: 72, 96: 96, 144: 144},
  '0.6827': {3: 2, 6: 5, 9: 7, 12: 10, 18: 16, 24: 22, 36: 33, 48: 45, 72: 68, 96: 91, 144: 138},
  '0.9545': {3: 0, 6: 2, 9: 4, 12: 7, 18: 11, 24: 16, 36: 26, 48: 37, 72: 58, 96: 80, 144: 124},
})

df_simulation_large2 = pd.DataFrame(**{'index': [3, 6, 9, 12, 18, 24, 36, 48, 72, 96, 144], 'columns': ['0.0500', '0.2000', '0.5000', '0.8000', '0.9500'], 'data': [[6, 4, 3, 2, 1], [10, 8, 6, 4, 2], [14, 11, 9, 6, 4], [18, 15, 12, 9, 7], [25, 22, 18, 14, 11], [32, 28, 24, 20, 16], [46, 41, 36, 31, 26], [60, 54, 48, 42, 37], [86, 79, 72, 65, 58], [112, 104, 96, 88, 80], [164, 154, 144, 134, 125]]})




results1= {
    6:{'0.1974':8,'0.2611':7,'0.3829':7,'0.5000':6,'0.6827':5,'0.9545':2,'0.9973':1,'0.9999':0},
    9:{'0.1974':11,'0.2611':11,'0.3829':10,'0.5000':9,'0.6827':7,'0.9545':4,'0.9973':2,'0.9999':0},
    12:{'0.1974':15,'0.2611':14,'0.3829':13,'0.5000':12,'0.6827':10,'0.9545':7,'0.9973':4,'0.9999':1},
    18:{'0.1974':22,'0.2611':21,'0.3829':19,'0.5000':18,'0.6827':16,'0.9545':11,'0.9973':7,'0.9999':4},
    24:{'0.1974':28,'0.2611':27,'0.3829':25,'0.5000':24,'0.6827':22,'0.9545':16,'0.9973':12,'0.9999':8},
    36:{'0.1974':41,'0.2611':40,'0.3829':38,'0.5000':36,'0.6827':33,'0.9545':26,'0.9973':21,'0.9999':16},
    48:{'0.1974':54,'0.2611':52,'0.3829':50,'0.5000':48,'0.6827':45,'0.9545':37,'0.9973':30,'0.9999':24},
    72:{'0.1974':79,'0.2611':77,'0.3829':74,'0.5000':72,'0.6827':68,'0.9545':58,'0.9973':50,'0.9999':42},
    96:{'0.1974':104,'0.2611':102,'0.3829':99,'0.5000':96,'0.6827':91,'0.9545':80,'0.9973':70,'0.9999':61},
    144:{'0.1974':154,'0.2611':152,'0.3829':147,'0.5000':144,'0.6827':138,'0.9545':124,'0.9973':112,'0.9999':101}
}



def lowest_mined(df):
    retval = len(df['mvs'][::-1])
    for i, val in df['mvs'][::-1].iteritems():
        if val != 0:
            return retval
        retval = i
    return retval


def simulate_all(fa_start, fa_delta, mvs=1.0, timeit=False):
    results2 = {}
    for nmean, probs in results1.items():
        results2[nmean] = dict()
        for p, nblocks in probs.items():
            if nblocks == 0:
                results2[nmean][p] = None
            else:
                st = time.time()
                steps = simulate_simple(fa_start, fa_delta, nmeans=nmean, nblocks=nblocks, mvs=mvs)
                feeagg_post_sim = steps[-1][1]
                
                results2[nmean][p] = lowest_mined(feeagg_post_sim)
                if timeit:
                    results2[nmean][p] = time.time()-st
    return results2




def txpool_from_getblocktemplate(blocktemplate):
    txs = dict()

    woven_ids = set()
    for i, mtx in enumerate(blocktemplate['transactions']):
        if len(mtx['depends']):
            [woven_ids.add(n) for n in mtx['depends']]
            woven_ids.add(i)

    for i, tx in enumerate(blocktemplate['transactions']):
        txs[tx['txid']] = {
            "vsize":  math.ceil(tx['weight']/4),
            "satoshi": tx['fee'],
            "feerate": tx['fee'] / math.ceil(tx['weight']/4),
            "position": i,
            "is_leaf": len(tx['depends']) == 0,
            "is_woven": i in woven_ids,
            "has_witness": tx['txid'] != tx['txid'],
        }
    return pd.DataFrame.from_dict(txs, orient="index")

def annotate_feerate(df_feeagg, typical_vsize=225, btc_price=8192):
    retval = df_feeagg.assign(
        feerate= np.round(np.exp(df_feeagg.index / 100), 3),
        typical_usd= np.round(np.exp(df_feeagg.index / 100) * typical_vsize * 1e-8 * btc_price, 2)
    )
    return retval


def annotate_rcs(df_feeagg, columns=None):
    return pd.concat([
        df_feeagg,
        df_feeagg[::-1].cumsum().add_prefix('rcs_')
    ], axis=1)


def fa_ceilgroup(df, div=40):
    nidx = np.arange(800,-div,-div)
    series = []
    for n,idx in enumerate(nidx):
        if idx == 0:
            s = df[df.index == 0].sum()
        else:
            s = df[np.logical_and(df.index <= idx, nidx[n+1] < df.index)].sum()
        series.append(s)    
    return pd.DataFrame(series, index=nidx) 



def pqload_lastn(prefix, suffix='full', n=1):
    folder = pathlib.Path(prefix)
    
    paths = []
    names = []
    retval = {}
    
    for el in reversed(sorted(folder.glob(f'*_{suffix}.parq'))):
        paths.append(el)
        names.append(el.name)
        retval[el.name] = pq.read_table(str(el)).to_pandas()
        
        if len(paths) >= n:
            break
    
    return retval


def pqload_lastn_date(date, suffix='full', n=1):

    PATH_PREFIX=(date-datetime.timedelta(0)).strftime('data/%Y/%m/%d/') 
    PATH_PREFIX_24=(date-datetime.timedelta(1)).strftime('data/%Y/%m/%d/') 

    last_day = list(pathlib.Path(PATH_PREFIX_24).glob(f'*_{suffix}.parq'))
    this_day = list(pathlib.Path(PATH_PREFIX).glob(f'*_{suffix}.parq'))
    
    paths = []
    names = []
    retval = {}
    
    for el in reversed(sorted(last_day + this_day)):
        paths.append(el)
        names.append(el.name)
        retval[el.name] = pq.read_table(str(el)).to_pandas()
        
        if len(paths) >= n:
            break
    
    return retval


def paths_lastn_date(date, suffix='full', n=1):

    PATH_PREFIX=(date-datetime.timedelta(0)).strftime('data/%Y/%m/%d/') 
    PATH_PREFIX_24=(date-datetime.timedelta(1)).strftime('data/%Y/%m/%d/') 

    last_day = list(pathlib.Path(PATH_PREFIX_24).glob(f'*_{suffix}.parq'))
    this_day = list(pathlib.Path(PATH_PREFIX).glob(f'*_{suffix}.parq'))
        
    return list(reversed(sorted(last_day + this_day)))[:n]



