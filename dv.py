import select, socket, sys
import threading
import time

listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_list = []
graph = []
packs = -1
number_of_neighbors = 0
neighbor_ip_and_port = []
update_interval = 0
master_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
master_ip_port = (None, None)

# function that receives a file and then reads the contents and saves them in corresponding variables
def readTopology(topo):
    # array of servers
    global server_list
    # array of costs for edges
    global graph
    global number_of_neighbors
    vertices = 0

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

    #going through and saving the servers to an array
    for x in range(2, vertices+2):
        server_list.append(txt_lines[x].split())

    # grabbing the port for this specific client/server
    serverPort = server_list[0][2]

    #going through and grabbing the costs for each server and neighbor pair
    for x in range(vertices+2, number_of_neighbors+vertices+2):
        graph.append((txt_lines[x].split()))
    # calling method to create neighbors ip and port
    create_neighbors_ip_and_port()

    return serverPort


class UdpServer:
    def __init__(self, port):
        host = socket.gethostname()
        global master_ip_port
        master_ip_port = (socket.gethostbyname(host), port)
        # socket used throughout udp to receive messages
        self.listening_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.listening_sock.bind((host, port))
        except WindowsError:
            print('Failed to create socket')
            exit()
        #add the run method to another thread
        udp_listening_thread = threading.Thread(target=self.run())
        udp_listening_thread.daemon = True
        udp_listening_thread.start()
        # thread to send periodic message(routing updates)
        periodic_thread = threading.Thread(target=periodic)
        periodic_thread.daemon = True
        periodic_thread.start()
        menu()

    def run(self):
        # listening port is added on a thread
        udp_listening_thread = threading.Thread(target=self.handler, args=(self.listening_sock,))
        udp_listening_thread.daemon = True
        udp_listening_thread.start()
    # handler recieves messages
    def handler(self, sock):
        while True:
            global packs
            packs = packs + 1
            data, addr = sock.recvfrom(1024)
            msg = data.decode("utf-8")
            # getting rid everything that is not a number
            msg = msg.replace(',', '')
            msg = msg.replace(']', '')
            msg = msg.replace('[', '')
            msg = msg.replace("'", "")
            #split msg by blank space
            b4_split = msg.split(' ')
            # grabs server id of sender
            sender_port = b4_split[1]
            server_id = findIPwithPort(sender_port)
            b4_split = b4_split[3:]
            # list of costs from the message
            costs = []
            # list of where they occurred in the message
            costs_at = [3, 7, 11, 15]
            # list of serverid2 from the message
            server_id_2 = []
            # list of where they occurred in the message
            server_id_2_at = [2, 6, 10, 14]
            for x in costs_at:
                costs.append(b4_split[x])
            for x in server_id_2_at:
                server_id_2.append(b4_split[x])
            graphAppender(server_id_2, costs)

            print("RECEIVED MESSAGE FROM SERVER ", server_id)

#find ip address with port number
def findIPwithPort(port):
    for x in server_list:
        if int(x[2]) == int(port):
            return x[0]

# grabs the server and cost that correlate to each other
# then puts them into a dictionary to make it easier
# to append them to the graph list
def graphAppender(s2, costs):
    global graph
    #combining the two arrays into a dict
    mapped = dict(zip(s2,costs))
    length = len(s2) +1
    cID = 0
    # finding the server id corresponding to the data it belongs to
    for i in range(1,length):
        if mapped[str(i)] == '0':
            cID = i

    # going through the dictionary checking if there is an INF and a 0
    # because we do not want to append these to the list
    # once were done checking we check if the data we are about to append
    #is not already in the list if not we append to the list
    for i in range(1,length):
        if mapped[str(i)] != 'inf' and mapped[str(i)] != '0':
            ary = [str(cID),str(i),mapped[str(i)]]
            if graphChecker(ary) == False:
                graph.append([str(cID),str(i),mapped[str(i)]])

#simple function checking the graph to see if the data that is about to appended is
#or is not in the graph already
def graphChecker(ary):
    isIn = False
    for x in graph:
        if x[0] == ary[0] and x[1] == ary[1] and x[2] == ary[2]:
            isIn = True
    return isIn

# gets ip address and port number and adds to a list of tuples
def create_neighbors_ip_and_port():
    global neighbor_ip_and_port
    global number_of_neighbors
    for neighbor in graph:
        for server in server_list:
            x = (server[1],int(server[2]))
            if neighbor[1] == server[0] and x not in neighbor_ip_and_port and x != master_ip_port:
                #change server[1] to ur ip address
                neighbor_ip_and_port.append((server[1], int(server[2])))
    return neighbor_ip_and_port

# bell man ford algorithm
def bellManFord(node, vertices):
    vertices = int(vertices)
    # initiating the array to have all inf
    calcs = [float("Inf")] * vertices
    # then changing the known node to 0 since the cost to itself is 0
    calcs[node] = 0

    # doing this for the amount of vertices
    for i in range(3):
        # then going through the edges and finding out the best cost path
        # graph contains all the edges
        for x, y, z in graph:
            if calcs[int(x)-1] != float("Inf") and calcs[int(x)-1] + int(z) < calcs[int(y)-1]:
                calcs[int(y)-1] = calcs[int(x)-1] + int(z)

    return calcs

#finds the amount of vertices depending on what information has been
#input to the graph
def verticesFinder():
    vertices = 0
    for x,y,z in graph:
        if x > y and int(x) > int(vertices):
            vertices = x
        elif y > x and int(y) > int(vertices):
            vertices = y
    return vertices

# creates the full cost table after going through the bellman forde algorithm
def generateTable():
    vertices = verticesFinder()
    table = []
    for i in range(int(vertices)):
        row = bellManFord(i,vertices)
        table.append(row)
    return table
# function that puts all the needed information to be sent to the other servers
# in the needed format
def message_format():
    msg_format = []
    table = generateTable()
    master_server_id = 9999
    # finding the server id of this class
    for x in server_list:
        if int(x[2]) == master_ip_port[1]:
            master_server_id = int(x[0])

    # num_of_update_fields
    msg_format.append(number_of_neighbors)
    # server_port
    msg_format.append(master_ip_port[1])
    # server_ip
    msg_format.append(master_ip_port[0])
    for x in server_list:
        if int(x[2]) == master_ip_port[1]:
            nth_server = [x[1], int(x[2]), int(x[0]), 0]
        else:
            # check if we a cost for specific server id. if true: add cost, Else: add 'inf'
            if find_cost(int(x[0])):
                nth_server = [x[1], int(x[2]), int(x[0]), table[master_server_id - 1][int(x[0]) - 1]]
            else:
                nth_server = [x[1], int(x[2]), int(x[0]), float("Inf")]
        for x in nth_server:
            msg_format.append(x)
    return msg_format

# function that finds the cost depending on the server received
def find_cost(server_num):
    cond = False
    for x in graph:
        if server_num == int(x[1]):
            cond = True
    return cond

#sends the message to all the servers when called in the menu
def step():
    msg_format = message_format()
    neighs = create_neighbors_ip_and_port()
    for x in neighs:
        master_socket.sendto((bytes(str(msg_format), "utf-8")), x)
    global packs
    packs = 0
    print("step SUCCESS")
    menu()

#does a periodic update with the specified interval
def periodic():
    while True:
        neighs = create_neighbors_ip_and_port()
        msg_format = message_format()
        time.sleep(update_interval)
        for x in neighs:
            master_socket.sendto((bytes(str(msg_format), "utf-8")), x)




#prints out the amount of packets received
def packets():
    print("packets SUCCESS")
    print("Number of distance vector packets received since last invocation: ", packs)
    menu()

#uses the bellford algorithm and then prints out the tables
def display():
    print("display SUCCESS")
    tableInfo = generateTable()
    print("\t\t  Routing Table")
    print("-----------------------------------------------")
    print("Destination Server \t Hop Server \t Cost")
    index = 1
    for i in tableInfo:
        count = 1
        for x in i:
            print(index, "\t\t\t", count, "\t\t", x)
            count+=1
        index+=1
    print("-----------------------------------------------")
    menu()

#finds the server Id
def findServerID():
    serverID = server_list[0][0]
    return serverID

#disables the connection of a node by deleting all information corresponding to that ip and port
def disable(senString):
    info = senString.split(" ")
    dID = info[1]
    serverID = findServerID()
    isNeighbor = isNeighborCheck(serverID, dID)
    if isNeighbor == True:
        master_socket.shutdown(socket.SHUT_RD)
        #master_socket.close()
        print(senString, "SUCCESS")
    elif isNeighbor == False:
        print(senString, "Error specified server is not a neighbor.")
    menu()

#simple check to see if the two servers are neighbors of each other
def isNeighborCheck(id, oID):
    isNeighbor = False
    for x,y,z in graph:
        if int(x) == int(id) and int(y) == int(oID):
            isNeighbor = True
    return isNeighbor

#simulates a crash
def crash():
    master_socket.close()
    print("crash SUCCESS")
    exit()
    menu()

#simple menu that listens for commands through out the whole time the program is being run
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

# updates the cost for a edge depending on the 2 serves inputed
def update(input):
    info = input.split(" ")
    server1 = info[1]
    server2 = info[2]
    cost = info[3]
    replace_cost(server1, server2, cost)
    print(info, "SUCCESS")
    menu()

#called from update which receives the 2 servers and the cost
#and then finds the two servers in the graph and then changes the cost
#to the desired cost
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

#the main function that stars it all
def main(fileName, interval):
    global update_interval
    update_interval = int(interval)
    serverPort = readTopology(fileName)
    udpServer = UdpServer(int(serverPort))


# py chat.py -t topo -i 3
#this is where we grab the command line arguments on the first launch
if __name__ == "__main__":
    main(sys.argv[2], int(sys.argv[4]))



