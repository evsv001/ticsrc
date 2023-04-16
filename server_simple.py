#!/usr/bin/python3
# -*- coding:utf-8 -*-
# 20230403 简化tcp传输
__author__ = 'Tic'
__version__ = '20230403'

print('ver:', __version__)
import socket, struct, os,  time
import json, threading

TcpPort = 9999

base_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(base_dir, 'download')

print("path:", base_dir)

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

myname = socket.getfqdn(socket.gethostname())
TIP = get_host_ip() 


class MYTCPServer:
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    allow_reuse_address = False
    max_packet_size = 8192
    coding = 'utf-8'
    request_queue_size = 5

    def __init__(self, server_address, bind_and_activate=True):
        """Constructor.  May be extended, do not override."""
        self.server_address = server_address
        self.socket = socket.socket(self.address_family, self.socket_type)
        if bind_and_activate:
            try:
                self.server_bind()
                self.server_activate()
            except:
                self.server_close()
                raise

    def server_bind(self):
        """Called by constructor to bind the socket.
        """
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind(self.server_address)
            self.server_address = self.socket.getsockname()
        except:
            self.socket.close()
            return

    def server_activate(self):
        self.socket.listen(self.request_queue_size)

    def server_close(self):
        self.socket.close()

    def get_request(self):
        return self.socket.accept()

    def close_request(self, request):
        request.close()

# run --------------------------------------------------
    def run(self):
        print('TCP server is running ....... ', TcpPort, '[', TIP, ']')
        while True:
            self.conn, self.client_addr = self.get_request()
            print('-- client : ', self.client_addr)
            while True:
                try:
                    head_struct = self.conn.recv(4)  
                    if not head_struct: break

                    head_len = struct.unpack('i', head_struct)[0] 
                    head_json = self.conn.recv(head_len).decode(self.coding)
                    head_dic = json.loads(head_json) 

                    cmd = head_dic['cmd']
                    print("  --- cmd :", cmd)
                    print("  ---     :", head_dic)
                    if hasattr(self, cmd):
                        func = getattr(self, cmd)
                        func(head_dic)

                except Exception:
                    break
# --------------------------------------------------
    def put(self, args):
        buff = 1024 * 256  # 每次接收的数据大小为256KB
        date = time.strftime("P%y%m%d",time.localtime()) 
        file_path = os.path.normpath(
            os.path.join(base_dir, date + args['filename']))

        filesize = int(args['filesize'])
        recv_size = 0
        with open(file_path, 'wb') as f:
            while recv_size < filesize:
                recv_data = self.conn.recv(buff)
                f.write(recv_data)
                recv_size += len(recv_data)
            else:
                print('      -->  %s (%sB) ' %
                      (str(recv_size), recv_size))
# list --------------------------------------------------
    def list(self, args):
        print("      --- " + args['filename'])
        base_dir = args['filename']
        result = os.listdir(base_dir)
        s = ""
        for file in result:
            filesize = os.path.getsize(base_dir + "/" + file)
            filetime = time.ctime(os.path.getmtime(base_dir + "/" +
                                                   file))  
            ttt = time.strptime(filetime, "%a %b %d %H:%M:%S %Y")  
            tt = time.strftime("%Y.%m.%d %H:%M:%S", ttt)  

            filestr = file + " -- " + str(filesize) + " --  " + str(tt)
            s += filestr + "\n"
        bdic = s.encode(self.coding)  
        dic_len = len(bdic)  
        bytes_len = struct.pack('i', dic_len)  
        self.conn.send(bytes_len)  
        self.conn.send(bdic)  
        print("      --- list: ok")

    def get(self, args):
        buff = 1024 * 256  
        filename = args['filename']  
        dic = {}
        if os.path.isfile(base_dir + '/' + filename) :  
            dic['filesize'] = os.path.getsize(base_dir + '/' + filename)
            dic['isfile'] = True
        else:
            dic['isfile'] = False
        str_dic = json.dumps(dic)  
        bdic = str_dic.encode(self.coding) 
        dic_len = len(bdic)
        bytes_len = struct.pack('i',
                                dic_len)  
        self.conn.send(bytes_len)  
        self.conn.send(bdic)  
        pp = 0
        if dic['isfile']:
            with open(base_dir + '/' + filename, 'rb') as f:
                while dic['filesize'] > buff:  
                    content = f.read(buff)
                    self.conn.send(content)
                    dic['filesize'] -= len(content)
                    pp += 1
                    if (pp % 40 == 0):
                        print(pp / 40 * 10, end='MB ')
                else:
                    content = f.read(buff)
                    self.conn.send(content)
                    dic['filesize'] -= len(content)
            print('      <-- download ok')
        else:
            print("      --- kl : error")

def show_help():
    print('TCP------------')
    print('    put: put filename kl')
    print('    get: get filename kl')
    print('    list: list')

def beginTCP():
    t1 = threading.Thread(
        target=TcpServer.run,
        args=()) 
    t1.start()

if __name__ == '__main__':

    TcpServer = MYTCPServer((TIP, TcpPort))
    show_help()
    beginTCP()
