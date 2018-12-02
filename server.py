import select, socket, sys
import threading
import time

listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
UDP_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_list = []
graph = []
packs = 0
number_of_neighbors = 0
neighbor_ip_and_port = []
neighbor_sockets = []
client_sockets = []
update_interval = 0
vertices = 0
mess = ""
master_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
master_ip_port = (None, None)

# function that receives a file and then reads the contents and saves them in corresponding variables
def readTopology(topo):
    # array of servers
    global server_list
    # array of costs for edges
    global graph
    global number_of_neighbors
    global vertices

    # grabbing the file and reading each line
    top = open(topo+".txt", "r")
    txt_lines = []
    txt_file = top.readlines()

    # read file while omitting "\n"
    for l in txt_file:
        txt_lines.append(l.rstrip('\n'))

    # cast needed to use in for loop
    vertices = int(txt_lines[0])
    number_of_neighbors = int(txt_lines[1])

    for x in range(2, vertices+2):
        server_list.append(txt_lines[x].split())

    # grabbing the port for this specific client/server
    serverPort = server_list[0][2]

    for x in range(vertices+2, number_of_neighbors+vertices+2):
        graph.append((txt_lines[x].split()))
    # new
    create_neighbors_ip_and_port()

    return serverPort

class UdpServer:
    def __init__(self, port):
        host = socket.gethostname()
        global master_ip_port
        master_ip_port = (socket.gethostbyname(host), port)
        self.listening_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.listening_sock.bind((host, port))
        except WindowsError:
            print('Failed to create socket')
            exit()
        udp_listening_thread = threading.Thread(target=self.run())
        udp_listening_thread.daemon = True
        udp_listening_thread.start()
        # thread to send periodic message(routing updates)
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
            global mess
            global packs
            packs = packs + 1
            data, addr = sock.recvfrom(1024)
            #print('Message from: ', addr)
            mess = data.decode("utf-8")
            #print('Message: ', data.decode("utf-8"))


# gets ip address and port number and adds to a list of tuples
def create_neighbors_ip_and_port():
    global neighbor_ip_and_port
    global number_of_neighbors
    for neighbor in graph:
        for server in server_list:
            if neighbor[1] == server[0]:
                #change server[1] to ur ip address
                neighbor_ip_and_port.append((server[1], int(server[2])))

# bell man ford algorithm
def bellManFord(node):
    # initiating the array to have all inf
    calcs = [float("Inf")] * vertices
    # then changing the known node to 0 since the cost to itself is 0
    calcs[node] = 0

    # doing this for the amount of vertices
    for i in range(vertices-1):
        # then going through the edges and finding out the best cost path
        # graph contains all the edges
        for x, y, z in graph:
            if calcs[x-1] != float("Inf") and calcs[x-1] + z < calcs[y-1]:
                calcs[y-1] = calcs[x-1] + z
            # if calcs[int(x)-1] != float("Inf") and calcs[int(x)-1] + int(z) < calcs[int(y)-1]:
            #     calcs[int(y)-1] = calcs[int(x)-1] + int(z)

    return calcs

# creates the full cost table after going through the bellman forde algorithm
def generateTable():
    table = []
    for i in range(vertices):
        row = bellManFord(i)
        table.append(row)
    return table

def message_format():
    msg_format =[]
    table = generateTable()
    master_server_id = 9999
    # finding the server id of this class
    for x in server_list:
        if int(x[2]) == master_ip_port[1]:
            master_server_id = int(x[0])
    #num_of_update_fields
    msg_format.append(number_of_neighbors)
    #server_port
    msg_format.append(master_ip_port[1])
    #server_ip
    msg_format.append(master_ip_port[0])
    for x in server_list:
        if int(x[2]) == master_ip_port[1]:
            nth_server = [x[1], int(x[2]), int(x[0]), 0]
        else:
            nth_server = [x[1], int(x[2]), int(x[0]), table[master_server_id-1][int(x[0])-1]]
        msg_format.append(nth_server)
    for xx in msg_format:
        print(xx)
    return msg_format


def step():
    print('this is step')
    print(generateTable())
    menu()

def periodic():
    while True:
        #msg_format = message_format()
        time.sleep(update_interval)
        for x, y in zip(neighbor_ip_and_port, graph):
            master_socket.sendto((bytes(str(y[0]), "utf-8")), (x[0], x[1]))

def packets():
    print("Number of distance vector packets received since last invocation: ", packs)
    menu()

def display():
    print("This is display")
    print(generateTable())
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
        elif listener == 'print':
            print(mess)
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
    for x in graph:
        if x[0] == server1 and x[1] == server2 or x[0] == server2 and x[1] == server1:
            if cost == "inf":
                print('Replacing cost in ', x)
                x[2] = float("Inf")
                print('New cost: ', x)
            else:
                print('Replacing cost in ', x)
                x[2] = cost
                print('New cost: ', x)

def main(fileName, interval):
    global update_interval
    update_interval = int(interval)
    serverPort = readTopology(fileName)
    #myServer = Server(int(serverPort))
    udpServer = UdpServer(int(serverPort))


# py chat.py topo 3
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])


