import select, socket, sys
import threading
import time

listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

peers = []
server_list = []
neighbor_cost_list = []
number_of_neighbors = 0
neighbor_ip_and_port = []
neighbor_sockets = []
client_sockets = []
update_interval = 0
master_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
master_ip_port = (None, None)

# function that receives a file and then reads the contents and saves them in corresponding variables
def readTopology(topo):
    # array of servers
    global server_list
    # array of costs for edges
    global neighbor_cost_list
    neighbor_cost_list = []
    global number_of_neighbors

    # grabbing the file and reading each line
    top = open(topo+".txt", "r")
    txt_lines = []
    txt_file = top.readlines()

    # read file while omitting "\n"
    for l in txt_file:
        txt_lines.append(l.rstrip('\n'))

    # cast needed to use in for loop
    number_of_servers = int(txt_lines[0])
    number_of_neighbors = int(txt_lines[1])

    for x in range(2, number_of_servers+2):
        server_list.append(txt_lines[x].split())

    # grabbing the port for this specific client/server
    serverPort = server_list[0][2]

    for x in range(number_of_servers+2, number_of_neighbors+number_of_servers+2):
        neighbor_cost_list.append((txt_lines[x].split()))
    # new
    create_neighbors_ip_and_port()

    return serverPort




class UdpServer:
    def __init__(self, port, interval):
        host = socket.gethostname()
        global master_ip_port
        global update_interval
        update_interval = interval
        master_ip_port = (host, port)
        self.listening_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.listening_sock.bind((host, port))
        except WindowsError:
            print('Failed to create socket')
            exit()
        udp_listening_thread = threading.Thread(target=self.run())
        udp_listening_thread.daemon = True
        udp_listening_thread.start()
        #thread to send periodic message(routing updates)
        periodic_thread = threading.Thread(target=periodic)
        periodic_thread.daemon = True
        periodic_thread.start()
        menu()

    # idk why we need a middle man thread but it wouldn't work if i made a thread for the handler in the init
    def run(self):
        udp_listening_thread = threading.Thread(target=self.handler, args=(self.listening_sock,))
        udp_listening_thread.daemon = True
        udp_listening_thread.start()
    # receives messages
    def handler(self, sock):
        while True:
            data, addr = sock.recvfrom(1024)
            print('Message from: ', addr)
            print('Message: ', data.decode("utf-8"))



# gets ip address and port number and adds to a list of tuples
def create_neighbors_ip_and_port():
    global neighbor_ip_and_port
    global number_of_neighbors
    for neighbor in neighbor_cost_list:
        for server in server_list:
            if neighbor[1] == server[0]:
                #change server[1] to ur ip address
                neighbor_ip_and_port.append((server[1], int(server[2])))


def step():
    print('this is step')
    menu()


def periodic():
    while True:
        time.sleep(update_interval)
        for x in neighbor_ip_and_port:
            master_socket.sendto((bytes('periodic message', "utf-8")), (x[0], x[1]))




def packets():
    print("This is packets")
    menu()


def display():
    print("This is display")
    menu()


def disable(senString):
    print("This is disable")
    menu()


def crash():
    print("This is crash. Bye")
    exit()
    menu()

def menu():
    valid_commands = ['update', 'step', 'packets', 'display', 'disable', 'crash', 'connect']
    print("MENU:")
    listener = input()
    listener = listener.lower()
    while True:
        if 'update' in listener:
            update(listener)
            print("This is update")
            break
        elif listener == 'step':
            step()
            break
        elif listener == 'packets':
            packets()
            break
        elif listener == 'display':
            display()
            break
        elif "disable" in listener:
            disable(listener)
            break
        elif listener == 'crash':
            crash()
            break
        elif listener not in valid_commands:
            invalid()
            break


# just says invalid command when an invalid command was input in the program
def invalid():
    print("Error Invalid command")
    menu()


def update(input):
    info = input.split(" ")
    server1 = info[1]
    server2 = info[2]
    cost = info[3]
    replace_cost(server1, server2, cost)
    menu()


def replace_cost(server1, server2, cost):
    for x in neighbor_cost_list:
        if x[0] == server1 and x[1] == server2:
            print('Replacing cost in ', x)
            x[2] = cost
            print('New cost: ', x)


def main(fileName, interval):
    serverPort = readTopology(fileName)
    #myServer = Server(int(serverPort))
    udpServer = UdpServer(int(serverPort), int(interval))
    print('DONE')



# py chat.py topo 3
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])


