import select, socket, sys
from time import sleep
import threading

listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
peers = []
server_list = []
neighbor_cost_list = []
number_of_neighbors = 0
neighbor_ip_and_port = []
neighbor_sockets = []
client_sockets = []


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


# server class that creates a server for each client that is launched
# that way each client is a user
class Server:
    # init method that starts off the server
    def __init__(self, port):
        # getting the host name (IP) using sockets
        host = socket.gethostname()
        try:
            # setting the ip and port to a socket
            listening_socket.bind((host, port))
        except WindowsError:
            print('Failed to create socket')
            exit()
        # enable the server to accept connections by using sock.listen
        listening_socket.listen(1)
        # creating a thread for the run function
        listening_thread = threading.Thread(target=self.run)
        # setting a thread to a daemon allows it to shut down while there are still threads running
        listening_thread.daemon = True
        listening_thread.start()
        menu()

    # function that accepts the connection from the client and adds the connection to the list of sockets
    def run(self):
        while True:
            connection, address = listening_socket.accept()
            connection_thread = threading.Thread(target=self.connection_handler, args=(connection,))
            connection_thread.daemon = True
            connection_thread.start()
            peers.append(connection)
            print('The connection to peer ', connection.getpeername()[0], ' is successfully established ')

    # this is the part of code where the server receives the message from the client
    def connection_handler(self, connection):
        while True:
            # added try/except for when a client disconnects in a weird way
            try:
                data = connection.recv(1024)
                print('Message received from ', connection.getpeername()[0])
                #print('Sender’s Port: <', connection.getpeername()[1], '>')
                print('Message: ', data.decode("utf-8"))
            except socket.error:
                print('Peer ', connection.getpeername()[0], ' terminates the connection')
                if len(peers) > 0 and connection in peers:
                    peers.remove(connection)
                    connection.close()
                return
            # checks to see if it receiving data from a socket if is not receiving data the socket is then removed and closed
            if not data:
                print('Peer ', connection.getpeername()[0], ' terminates the connection')
                if len(peers) > 0 and connection in peers:
                    peers.remove(connection)
                    connection.close()
                break


# handles the client side of the program such as sending messages to the server, and connections
class Client:

    # this function initializes the client by creating a socket
    def __init__(self, ip_port):
        connecting_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print('Connecting...')
            # connects to the server and sends ip and port
            connecting_socket.connect(ip_port)
        except WindowsError:
            print('Connection failed.')
            return
        print('The connection to peer ', connecting_socket.getpeername()[0], ' is successfully established ')
        client_thread = threading.Thread(target=self.connection_handler, args=(connecting_socket,))
        client_thread.daemon = True
        client_thread.start()
        peers.append(connecting_socket)

    # handler used to receive the message from the server and then sends to a specific client
    # almost same as server handler
    def connection_handler(self, connection):
        while True:
            try:
                data = connection.recv(1024)
            except socket.error:
                print('Peer ', connection.getpeername()[0], ' terminates the connection')
                if len(peers) > 0 and connection in peers:
                    peers.remove(connection)
                    connection.close()
                return
            if not data:
                print('Peer ', connection.getpeername()[0], ' terminate the connection')
                if len(peers) > 0 and connection in peers:
                    peers.remove(connection)
                    connection.close()
                break
            print('Message received from ', connection.getpeername()[0])
            print('Sender’s Port: <', connection.getpeername()[1], '>')
            print('Message: ', data.decode("utf-8"))


# connects to all neighbors and check for duplicates
def connect():
    for x in neighbor_ip_and_port:
        if duplicate_socket_check(x):
            print('dup detected: ', x)
        else:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # add ip address for x[0]
                sock.connect((x[0], int(x[1])))
                neighbor_sockets.append(sock)
                print(sock.getpeername()[1], ' added')
            except:
                print('connection failed: ', x)
    menu()

# checks if neighbor is already connected
def duplicate_socket_check(x):
    dup = False
    for sockets in neighbor_sockets:
        if int(x[1]) == (sockets.getpeername()[1]):
            dup = True
    return dup

# gets ip address and port number and adds to a list of tuples
def create_neighbors_ip_and_port():
    global neighbor_ip_and_port
    global number_of_neighbors
    for neighbor in neighbor_cost_list:
        for server in server_list:
            if neighbor[1] == server[0]:
                neighbor_ip_and_port.append((server[1], server[2]))


def step():
    print('this is step')
    menu()


def send_packets():
    global neighbor_sockets
    if neighbor_sockets != []:
        for sock in neighbor_sockets:
            try:
                sock.send(bytes('poop', "utf-8"))
                print('message successfully sent')
            except:
                print('message NOT sent to', sock)
    else:
        print('no neighbors connected')


def packets():
    print("This is packets")
    send_packets()
    menu()


def display():
    print("This is display")
    print("The IP address is: ", listening_socket.getsockname()[0])
    print("The program runs on port ", listening_socket.getsockname()[1])
    for x in neighbor_cost_list:
        print('server: ', x)
    print(number_of_neighbors)
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
        elif listener == 'connect':
            connect()
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
    myServer = Server(int(serverPort))
    myServer.run()
    menu()


# py chat.py topo 3
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])


