import argparse
import pathlib
import pycoin.block

parser = argparse.ArgumentParser()

parser.add_argument('filename')
filename = parser.parse_args().filename

f = None
fout = None


def getblockinfo(f):
    blk = pycoin.block.Block.parse(f)
    txcount = len(blk.txs)
    coinbase_sat = blk.txs[0].total_out()        
    
    return [txcount, coinbase_sat]


for line in open(f'dataset-blocks/{filename}'):
    l = line.strip().split('\t')
    
    if not f:
        f=open(f"/root/.bitcoin/blocks/{l[2]}", 'rb')
        fout = open(f"dataset-blocks2/" + l[2].replace('.dat', '.tsv'), 'w')

    f.seek(int(l[3]))
    
    data = l + getblockinfo(f)
    
    fout.write('\t'.join(map(str, data)))
    fout.write('\n')

f.close()
fout.close()