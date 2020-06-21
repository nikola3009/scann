import binascii
import sys
import os
import threading
from queue import Queue
 
class FileChecker(threading.Thread):
    def __init__(self, queue, storage, pattern):
        threading.Thread.__init__(self)
        self.queue = queue
        self.storage = storage
        self.pattern = pattern
    
    def run(self):
        while True:
            filename = self.queue.get()
            self.check_file(filename)
            self.queue.task_done()

    def read_in_chunks(self, file_object, chunk_size=512):
        while True:
            data = file_object.read(chunk_size)
            if not data:
                break
            yield data

    def check_file(self, filename):
        with open(filename, 'rb') as f:
            for piece in self.read_in_chunks(f):
                hex_content = binascii.hexlify(piece)
                if self.pattern in hex_content:
                    self.storage.append((filename, True))
                    return
            self.storage.append((filename, False))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("ERROR")
        exit()

    directory = sys.argv[1]
    signature = bytes(str(sys.argv[2]), 'utf8')

    files = []
    tree = os.walk(directory)
    for node in tree:
        for f in node[2]:
            files.append(node[0] + "/" + f)
    
    num_threads = min(int(len(files)/5+1), 5)

    print("Start threads: ", num_threads, " signature:", signature.decode(), "in ", len(files), " files")

    queue = Queue()
    res = []

    for i in range(num_threads):
        t = FileChecker(queue, res, signature)
        t.setDaemon(True)
        t.start()
    
    for f in files:
        queue.put(f)
 
    queue.join()

    with open("out.txt","w+") as wf:
        for finding in res:
            if finding[1]:
                wf.write("<%s> - detected\r\n" % finding[0])
            else:
                wf.write("<%s> - undetected\r\n" % finding[0])
