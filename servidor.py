import socket
import sys
import time
import math

class Queue:
    #Constructor creates a list
    def __init__(self):
        self.queue = list()

    #Adding elements to queue
    def enqueue(self,data):
        #Checking to avoid duplicate entry (not mandatory)
        if data not in self.queue:
            self.queue.insert(0,data)
            return True
        return False

  #Removing the last element from the queue
    def dequeue(self):
        if len(self.queue)>0:
            return self.queue.pop()
        return ("Queue Empty!")

    #Getting the size of the queue
    def size(self):
        return len(self.queue)

    def remove(self, value):
        if str(value) in self.queue: self.queue.remove(str(value))
        if int(value) in self.queue: self.queue.remove(int(value))
        return True

    #printing the elements of the queue
    def printQueue(self):
        return self.queue

class Stack:
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return self.items == []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop()

    def peek(self):
        return self.items[len(self.items)-1]

    def size(self):
        return len(self.items)

#Instanitate CPU values
politicaCPU = "RR" #Round Robin
politicaMEM = "MFU" #Most Frequently used
quantum = 1.0 #quantum size in seconds
realMem = 3 #real memory size in kilonytes, 1 => 1024
swapMem = 4 #swap memory size in kilobytes, 1 => 1024
pageSizeInKB = 1 #page size in kilobytes, 1 => 1024
pageSizeInBytes = pageSizeInKB*1024
timestamp = 0.0
delta = quantum

pageTable = ["L"] * (realMem/pageSizeInKB) #lista con paginas inicialmente libres
mfuPageTable = Stack()
swapTable = ["L"] * (swapMem/pageSizeInKB) #lista de swap inicialmente libre
mfuSwapTable = Stack()
pQueue = Queue() #cola de listos
CPU = "L"
processID = 1
processSize = ["L"]
lastPageUsed = [0]
finished = []

def incrementTimestamp(time):
    global timestamp
    timestamp += time

def addPage(processID, pageID):
    global pageTable
    global lastPageUsed
    lastPageUsed[int(processID)] = int(pageID)
    proccessWithPage = str(processID) + "." + str(int(pageID))
    if proccessWithPage in pageTable:
       #nothing, page already loaded
       print("Page already in Real Memory")

    else:
        print("Page Fault in Real Memory")
        #memoria libre
        if "L" in pageTable:
            i = pageTable.index("L")
            pageTable[i] = proccessWithPage
            #memoria ocpada, necesidad de un swap
        else:
            print("Swap in page table, PENDING LOGIC")

        return str(pageTable.index(proccessWithPage)) + ":" + proccessWithPage

def addSwapPage(processID, pageID):
    global swapTable
    proccessWithPage = str(processID) + "." + str(int(pageID))
    if proccessWithPage in swapTable:
        # nothing, page already loaded
        print("Page already in Swap Memory")

    else:
        print("Page Fault in Swap Memory")
        # memoria libre
        if "L" in swapTable:
            i = swapTable.index("L")
            swapTable[i] = proccessWithPage
        # memoria ocpada, necesidad de un swap
        else:
            print("Swap in swap table, PENDING LOGIC")
    return str(swapTable.index(proccessWithPage)) + ":" + proccessWithPage

def addQueueProcToCPU():
    if(pQueue.size() != 0):
        global CPU
        topProcessID = pQueue.dequeue()
        tableEntry = addPage(topProcessID, lastPageUsed[topProcessID])
        CPU = (topProcessID)

def create(size):
    # global pQueue
    global processID
    global CPU
    processSize.append(int(math.ceil(float(size))))
    pQueue.enqueue(processID)
    lastPageUsed.append(0)


    #if first process
    if CPU == "L":
        addQueueProcToCPU()

    print >>sys.stderr, 'sending answer back to the client'
    answer = "%.3f process %s created size %s pages" % (timestamp, processID, processSize[processID])
    connection.sendall(answer)
    processID += 1

def address(processID, virtualAddress):
    #process not in CPU
    if (processID) not in str(CPU):
        message = "%.3f ERROR: Requested process ID not in CPU" % timestamp
        print(message)
        connection.sendall(message)
        return None
        #virtual address out of bounds
    if (processSize[int(processID)]*pageSizeInBytes) <= int(virtualAddress):
        message = "%.3f ERROR: Requested virtul address out of bounds" % timestamp
        print(message)
        connection.sendall(message)
        return None
    procPageID = math.floor(int(virtualAddress)/pageSizeInBytes)
    procByteNum = int(virtualAddress)%pageSizeInBytes
    tableEntry = addPage(processID, procPageID)
    pageEntry = (tableEntry.split(":"))[0]

    realAddress = int(pageEntry)*pageSizeInBytes + int(procByteNum)

    print >>sys.stderr, 'sending answer back to the client'
    answer = "%.3f real address: %s" % (timestamp, realAddress)
    connection.sendall(answer)

def quantumFunc():
    global CPU
    incrementTimestamp(float(quantum))

    if CPU != "L" and pQueue.size() != 0:
        #quitar proceso del CPU y poner otro
        pQueue.enqueue(CPU)
        addQueueProcToCPU()
    elif pQueue.size() != 0:
        #quitar proceso del CPU
        CPU = "L"
        #poner proceso en el CPU
        addQueueProcToCPU()


    print >>sys.stderr, 'sending answer back to the client'
    answer = "%.3f quantum end" % timestamp
    connection.sendall(answer)

def terminate(processID):
    #remove from queue
    global CPU
    pQueue.remove(processID)

    #remove from pageTable
    processName = str(processID) + "."
    processMatching = [s for s in pageTable if processName in s]
    for s in processMatching:
        i = pageTable.index(s)
        pageTable[i] = "L"

    #remove from swapTable
    processName = str(processID) + "."
    processMatching = [s for s in swapTable if processName in s]
    for s in processMatching:
        i = swapTable.index(s)
        pageTable[i] = "L"

    #remove from CPU
    if str(CPU) == str(processID):
        CPU = "L"
        addQueueProcToCPU()

    #add to finished list
    finished.append(processID)

    print >>sys.stderr, 'sending answer back to the client'
    answer = "%.3f process %s terminated" % (timestamp, processID)
    connection.sendall(answer)

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Then bind() is used to associate the socket with the server address. In this case, the address is localhost, referring to the current server, and the port number is 10000.

# Bind the socket to the port
server_address = ('localhost', 10000)
print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)


#Calling listen() puts the socket into server mode, and accept() waits for an incoming connection.

# Listen for incoming connections
sock.listen(1)


# Wait for a connection
print >>sys.stderr, 'waiting for a connection'
connection, client_address = sock.accept()

#accept() returns an open connection between the server and client, along with the address of the client. The connection is actually a different socket on another port (assigned by the kernel). Data is read from the connection with recv() and transmitted with sendall().

try:
    print >>sys.stderr, 'connection from', client_address

    # Receive the data
    while True:
        data = ""
        data = connection.recv(256)
        print("data:" + data)
        command = data
        comment = None
        parameters = []

        if "//" in command:
            commentSplit = data.split("//")
            command = commentSplit[0]
            comment = commentSplit[1]
        if " " in  command:
            parameters = command.split(" ")
            command = parameters[0]

        incrementTimestamp(0.001)
        print("data:" + data)
        print("command:" + command)
        #Create %s, size in pages
        if command == "Create":
            create(parameters[1])
        #Quantum
        elif command == "Quantum":
            quantumFunc()
        #Address
        elif command == "Address":
            address(parameters[1], parameters[2])
        #Fin
        elif command == "Fin":
            terminate(parameters[1])
        else:
            print("ningun commando")

        #End
        print("CPU:" + str(CPU))
        print("cola:"),
        print(pQueue.printQueue())
        print("finished:"),
        print(finished)
        print("pageTable:"),
        print(pageTable)
        print("swapTable:"),
        print(swapTable)

        if data == "End":
            print >>sys.stderr, 'no data from', client_address
            answer = "Server terminating"
            connection.sendall(answer)
            connection.close()
            sys.exit()
finally:
    # Clean up the connection
    print >>sys.stderr, 'se fue al finally'
    connection.close()

#When communication with a client is finished, the connection needs to be cleaned up using close(). This example uses a try:finally block to ensure that close() is always called, even in the event of an error.


def main(args):
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
