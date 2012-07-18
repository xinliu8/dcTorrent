from BitTornado.BT1.Storage import Storage
from BitTornado.BT1.StorageWrapper import StorageWrapper
from threading import Event
import os

def finished():
    print "Finished\n"

def failed():
    print "Failed\n"

def add_task(func, interval):
    pass

if __name__ == '__main__':
    doneflag = Event()
    file_path = ['tests/testStorageWrapper.txt']
    file_len = [1024]
    files = zip(file_path, file_len)
    num_pieces = 16
    piece_len = file_len[0]/num_pieces
    config = {'max_files_open': 10, 'write_buffer_size': 4, 'auto_flush': 0}
    storage = Storage(files, piece_len, doneflag, config)
    download_slice_size = piece_len/2
    pieces = [1] * num_pieces
    storage_wrapper = StorageWrapper(storage, download_slice_size, pieces, piece_len, finished, failed, backfunc= add_task, config = config)
    storage_wrapper.old_style_init()
    index = 15
    (begin, length) = storage_wrapper.new_request(index)
    assert begin==0 and length == download_slice_size
    (begin, length) = storage_wrapper.new_request(index)
    assert begin==download_slice_size and length == download_slice_size

    strdata = bytearray([index]*download_slice_size)
    result = storage_wrapper.piece_came_in(index, 0, strdata)
    assert result==True
    result = storage_wrapper.piece_came_in(index, 32, strdata)
    assert result==True
    assert storage_wrapper.do_I_have(index)==True
    print storage_wrapper.places
    print storage_wrapper.blocked
    print storage_wrapper.blocked_holes
    print storage_wrapper.blocked_movein
    print storage_wrapper.blocked_moveout