#!/bin/env python3
import struct
import hashlib
import pathlib

outpath = pathlib.Path('dataset-blocks')

for filepath in sorted(sorted(pathlib.Path('~/.bitcoin/blocks').expanduser().glob('blk*.dat'))):
    filename=filepath.name
    fileoutpath = outpath / filepath.name.replace('.dat', '.tsv')
    
    #print(filename)
    f = open(filepath, 'rb')
    fileout = open(fileoutpath, 'w')
    while True:
        
        r88 = f.read(88)
        start = f.tell() - 80
        if len(r88) < 88:
            break
        
        # skipping 0 bytes
        if r88[0] == 0:
            print(f'{filename}: skipped 0 bytes {start}')
            f.seek(start-8+1)
            continue
        
        [magic, size] = struct.unpack('II', r88[:8])
        if magic != 0xd9b4bef9:
            print (f'{filename}: invalid magic ({magic}) at position {start} / {filepath.stat().st_size}')
            break

        blk_hash = hashlib.sha256(hashlib.sha256(r88[8:]).digest()).digest()
        prv_hash = r88[8+4:8+4+32]
        [time] = struct.unpack('I', r88[8+4+32+32:8+4+32+32+4])
        fileout.write('\t'.join(map(str, [
            blk_hash[::-1].hex(), 
            prv_hash[::-1].hex(), 
            filename, 
            start, 
            size, 
            time,
        ])) + '\n')
        f.seek(start+size)
    f.close()
    fileout.close()