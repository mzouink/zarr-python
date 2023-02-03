
import pytest

from zarr.n5 import N5ChunkWrapper, N5FSStore
from zarr.creation import create
from zarr.storage import atexit_rmtree
from numcodecs import GZip
import numpy as np
from typing import Tuple
import shutil
import json
import atexit


def test_make_n5_chunk_wrapper():
    dtype = 'uint8'
    chunk_shape = (10,)
    codec = GZip()
    # ValueError when specifying both compressor and compressor_config
    with pytest.raises(ValueError):
        N5ChunkWrapper(dtype,
                       chunk_shape=chunk_shape,
                       compressor_config=codec.get_config(),
                       compressor=codec)

    wrapper_a = N5ChunkWrapper(dtype, chunk_shape=chunk_shape, compressor_config=codec.get_config())
    wrapper_b = N5ChunkWrapper(dtype, chunk_shape=chunk_shape, compressor=codec)
    assert wrapper_a == wrapper_b


@pytest.mark.parametrize('chunk_shape', ((2,), (4, 4), (8, 8, 8)))
def test_partial_chunk_decode(chunk_shape: Tuple[int, ...]):
    # Test that the N5Chunk wrapper can handle fractional chunks that
    # may be generated by other N5 implementations
    dtype = 'uint8'
    codec = GZip()
    codec_wrapped = N5ChunkWrapper(dtype, chunk_shape=chunk_shape, compressor=codec)
    subslices = tuple(slice(0, cs // 2) for cs in chunk_shape)
    chunk = np.zeros(chunk_shape, dtype=dtype)
    chunk[subslices] = 1
    subchunk = np.ascontiguousarray(chunk[subslices])
    assert np.array_equal(codec_wrapped.decode(codec_wrapped.encode(subchunk)), chunk)


def test_dtype_decode():
    path = 'data/array.n5'
    atexit.register(atexit_rmtree, path)
    n5_store = N5FSStore(path)
    create(100, store=n5_store)
    dtype_n5 = json.loads(n5_store[".zarray"])["dtype"]
    dtype_zarr = json.loads(create(100).store[".zarray"])["dtype"]
    assert dtype_n5 == dtype_zarr
