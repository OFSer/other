import os
import sys
import subprocess
from xmlrpc.server import SimpleXMLRPCServer

def collection_script(p):
    current_path = os.getcwd()
    exe = subprocess.Popen("python3 {}/dataCollection.py {}".format(current_path, p), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return

if __name__ == "__main__":
    para = sys.argv[1]
    server = SimpleXMLRPCServer(("{}".format(para), 9901), allow_none=True)  #此处IP为Server端IP
    server.register_function(collection_script)
    server.serve_forever()
