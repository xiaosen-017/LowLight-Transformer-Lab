"""Fetch only AlexNet convolution tensors from the official torchvision ZIP checkpoint."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import io
from pathlib import Path
import pickletools
import urllib.request
import zipfile

import numpy as np

URL = 'https://download.pytorch.org/models/alexnet-owt-7be5be79.pth'
SIZE = 244408911
END = SIZE - 1
SHAPES = {'0': (64, 3, 11, 11), '3': (192, 64, 5, 5), '6': (384, 192, 3, 3),
          '8': (256, 384, 3, 3), '10': (256, 256, 3, 3)}


def get_range(start, end):
    request = urllib.request.Request(URL+'?bytes=%d'%start, headers={'Range': 'bytes=%d-%d'%(start,end)})
    error = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(request,timeout=35) as response:
                if response.status != 206 or response.headers['Content-Range'] != 'bytes %d-%d/%d'%(start,end,SIZE):
                    raise ValueError('Unexpected Content-Range')
                payload = response.read()
                if len(payload) != end-start+1:
                    raise ValueError('Incomplete range')
                return payload
        except (OSError, ValueError) as caught:
            error = caught
    raise RuntimeError('AlexNet range download failed') from error


def fetch(output):
    # A sparse in-memory file keeps the original ZIP offsets. zipfile verifies
    # each extracted member's CRC. Pickle opcodes are inspected without loading it.
    class Archive(io.RawIOBase):
        def __init__(self, chunks):
            self.pos = 0
            self.chunks = chunks
        def seek(self, off, whence=0):
            self.pos = off if whence == 0 else (self.pos if whence == 1 else SIZE)+off
            return self.pos
        def tell(self):
            return self.pos
        def seekable(self):
            return True
        def read(self, size=-1):
            length = SIZE-self.pos if size < 0 else min(size,SIZE-self.pos)
            if length == 0:
                return b''
            for offset, data in self.chunks.items():
                if offset <= self.pos and self.pos+length <= offset+len(data):
                    start = self.pos-offset
                    self.pos += length
                    return data[start:start+length]
            raise ValueError('Requested bytes outside fetched ZIP members')

    tail = SIZE-65536
    chunks = {tail:get_range(tail,END), 0:get_range(0,16383)}
    def metadata(archive):
        return [arg for opcode,arg,_ in pickletools.genops(archive.read('archive/data.pkl'))
                if opcode.name == 'BINUNICODE']
    with zipfile.ZipFile(Archive(chunks)) as archive:
        words = metadata(archive)
        entries = {}
        for i, word in enumerate(words):
            if word.startswith('features.'):
                key = next(value for value in words[i+1:] if value.isdecimal())
                entries[word] = archive.getinfo('archive/data/'+key)
        def fill(item):
            start = item.header_offset
            return start, get_range(start,min(END,start+item.compress_size+192))
        with ThreadPoolExecutor(max_workers=8) as pool:
            chunks.update(pool.map(fill,entries.values()))
        arrays = {}
        for name, item in entries.items():
            _, layer, kind = name.split('.')
            shape = SHAPES[layer]
            arrays[name] = np.frombuffer(archive.read(item),dtype='<f4').reshape(shape if kind=='weight' else (shape[0],))
    if len(arrays) != 10:
        raise ValueError('Expected ten convolution weights and biases')
    with output.open('xb') as file:
        np.savez(file,**arrays)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    fetch(parser.parse_args().output)
