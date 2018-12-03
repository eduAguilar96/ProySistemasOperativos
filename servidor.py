import socket
import sys
import time
import math
import tabulate

#clase de Queue para la cola de listos
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

#clase de stack para MFU
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

    def printStack(self):
        return self.items

#Instanitate CPU values
#print('Politica Scheduling CPU = "RR"') #Round Robin
#print('Politica de Memoria = "MFU"') #Most Frequently used
quantum = 1.0 #quantum size in seconds
realMem = 3 #real memory size in kilonytes, 1 => 1024
swapMem = 4 #swap memory size in kilobytes, 1 => 1024
pageSizeInKB = 1 #page size in kilobytes, 1 => 1024

pageSizeInBytes = pageSizeInKB*1024
timestamp = 0.0

pageTable = ["L"] * (realMem/pageSizeInKB) #lista con paginas inicialmente libres
swapTable = ["L"] * (swapMem/pageSizeInKB) #lista de swap inicialmente libre

def setGlobals():
    global pageSizeInBytes
    pageSizeInBytes = pageSizeInKB*1024

    global pageTable
    pageTable = ["L"] * (int(realMem)/int(pageSizeInKB)) #lista con paginas inicialmente libres

    global swapTable
    swapTable = ["L"] * (int(swapMem)/int(pageSizeInKB)) #lista de swap inicialmente libre

mfuPageTable = Stack() #stack que guarda el order de las paginas
mfuSwapTable = Stack() #stack que guarda el order del swap
pQueue = Queue() #cola de listos

CPU = "L" #valor del CPU actual
processID = 1 #valor global de siguiente proceso
processSize = ["L"] #arreglo que guarda el tamano de los proceso
lastPageUsed = [0] #arreglo que guarda la ultima pagina utliada por cada proceso para cuando regresan al CPU
finished = [] #arreglo que guarda en orden los proceso que van finalizando
dirReal = 0 #valor global que sirve para desplegar la tabla

# Funcion que incrementa el valor global de Timestamp
def incrementTimestamp(time):
    global timestamp
    timestamp += time

#Funcion que agrega una pagina a la tabla de la Memoria Real
#parameters: processID, pageID
#regresa el valor que se llena en la table, ej: 0:1.2
def addPage(processID, pageID):
    #guardar el valor de la ultima pagina utlizada por el proceso en caso de que regrese al CPU
    lastPageUsed[int(processID)] = int(pageID)

    #este string es la concatenaccion del proceso con su pagina
    proccessWithPage = str(processID) + "." + str(int(pageID))
    print("proccessWithPage", proccessWithPage)

    #Si una pagina ya esta en memoria real
    if proccessWithPage in pageTable:
       #nada, la pagina ya esta cargada
       #guardar el orden
       mfuPageTable.push(proccessWithPage)
    #Si el proceso esta en el espaico de Swap
    elif proccessWithPage in swapTable:
        #quitar de la memoria de swap
        i = swapTable.index(proccessWithPage)
        swapTable[i] = "L"
        #re-llamar esta misma funcion para que ya lo ponga
        return addPage(processID, pageID)
    #Si no esta en memoria real
    else:
        #Si hay memoria libre
        if "L" in pageTable:
            i = pageTable.index("L")
            pageTable[i] = proccessWithPage
            mfuPageTable.push(proccessWithPage)
        #Si hay memoria ocupada, hacer un swap out
        else:
            #Encontrar el MFU valido
            notFound = True
            top = pageTable[0]
            while notFound:
                top = mfuPageTable.pop()
                if top in pageTable:
                    notFound = False
            #sacar el numero de proceso y numero de pagina
            splitSwapProc = top.split(".")
            #agregar ringlon a la memoria de swap
            addSwapPage(splitSwapProc[0], splitSwapProc[1])

            #remover ringlon de la memoria real
            i = pageTable.index(top)
            pageTable[i] = "L"
            #re-llamar funcion para ya agregar
            return addPage(processID, pageID)

    return str(pageTable.index(proccessWithPage)) + ":" + proccessWithPage

#Funcion que agrega una pagina a la tabla de la Memoriade Swap
#parameters: processID, pageID
#regresa el valor que se llena en la table, ej: 0:1.2
def addSwapPage(processID, pageID):
    #este string es la concatenaccion del proceso con su pagina
    proccessWithPage = str(processID) + "." + str(int(pageID))
    #Si el proceso esta en la memoria de Swap
    if proccessWithPage in swapTable:
        # nada, la pagina ya esta
        #guardar el orden para el MFU
        mfuSwapTable.push(proccessWithPage)
    #Si el proceso no esta en memoria de Swap
    else:
        # memoria libre
        if "L" in swapTable:
            #llenar ringlon en la tabla
            i = swapTable.index("L")
            swapTable[i] = proccessWithPage
            #guardar orden para MFU
            mfuSwapTable.push(proccessWithPage)
        # Si memoria ocupada, necesidad de un reemplazo
        else:
            #encontrar un MFU valido
            notFound = True
            top = swapTable[0]
            while notFound:
                top = mfuSwapTable.pop()
                if top in swapTable:
                    notFound = False

            #quitar ringlon de memoria swap
            i = swapTable.index(top)
            swapTable[i] = "L"
            #re-llamar metodo para ya poner ringlon
            return addSwapPage(processID, pageID)

    return str(swapTable.index(proccessWithPage)) + ":" + proccessWithPage

#Funcion que agrega el proceso enfrente de la cola de listos al CPU
def addQueueProcToCPU():
    if(pQueue.size() != 0):
        global CPU
        #sacar proceso listo
        topProcessID = pQueue.dequeue()
        #agregar pagina de nuevo proceso a memoria real
        tableEntry = addPage(topProcessID, lastPageUsed[topProcessID])
        #reemplazar proceso en el CPU
        CPU = topProcessID

#Funcion que crea un nuevo proceso
#parametros: size, en btyes
def create(size):
    # global pQueue
    global processID
    global CPU
    #agregar tamano de proceso al arreglo de tamanos
    processSize.append(int(math.ceil(float(int(size)/int(pageSizeInBytes)))))
    #agregarlo a la cola de listos
    pQueue.enqueue(processID)
    #inicializar que su ultima pagina en ser usada fue la 0
    lastPageUsed.append(0)


    #Si es el primer proceso cargarlo al CPU
    if CPU == "L":
        addQueueProcToCPU()

    print >>sys.stderr, 'sending answer back to the client'
    answer = "%.3f process %s created size %s pages" % (timestamp, processID, processSize[processID])
    connection.sendall(answer)

    #incrementar contador de procesos
    processID += 1

#Funcion que saca la direccion real al igual que carga dicha en en CPU de un proceso especifico
#Parametros, processID, virtualAddress
def address(processID, virtualAddress):
    #Si el proceso no en CPU, ignorar
    if (processID) not in str(CPU):
        message = "%.3f ERROR: Requested process ID not in CPU" % timestamp
        connection.sendall(message)
        return None
    #Si el proceso esta fuera del tmano, ignorar
    if (processSize[int(processID)]*pageSizeInBytes) <= int(virtualAddress):
        message = "%.3f ERROR: Requested virtul address out of bounds" % timestamp
        connection.sendall(message)
        return None
    #obtener el numero de pagina de acuerdo a la dir virtual
    procPageID = int(math.floor(int(virtualAddress)/pageSizeInBytes))
    #sacar el byte especifico que sobra despues de obtener el numero de pag
    procByteNum = int(virtualAddress)%pageSizeInBytes
    #agregar pagina a la memoria real y/o obtener su entrada en la tabla
    print(processID, procPageID)
    tableEntry = addPage(processID, procPageID)
    print(tableEntry)
    #obtener el indice que tiene dicha pagina en la memoria real
    pageEntry = (tableEntry.split(":"))[0]
    #calcualr la dir real
    realAddress = int(pageEntry)*pageSizeInBytes + int(procByteNum)
    global dirReal
    dirReal = realAddress

    print >>sys.stderr, 'sending answer back to the client'
    answer = "%.3f real address: %s" % (timestamp, realAddress)
    connection.sendall(answer)

#Funcion que simula un quantum
def quantumFunc():
    global CPU
    #incrementar el timestamp por un quantum
    incrementTimestamp(float(quantum))

    #si el CPU esta ocupado y procesos esperar...
    if CPU != "L" and pQueue.size() != 0:
        #quitar proceso del CPU y poner otro
        pQueue.enqueue(CPU)
        addQueueProcToCPU()
    #Si el CPU esta vacio pero hay procesos esperando...
    elif pQueue.size() != 0:
        #quitar proceso del CPU
        CPU = "L"
        #poner proceso en el CPU
        addQueueProcToCPU()
    #En dado caso que el CPU no este vacio, pero asimismo no haya procesos en espera, se queda igual

    print >>sys.stderr, 'sending answer back to the client'
    answer = "%.3f quantum end" % timestamp
    connection.sendall(answer)

#Funcion que simula la terminacion de un proceso
#parametros: processID
def terminate(processID):
    #quitar proceso de la cola de listos
    global CPU
    pQueue.remove(processID)

    #quitar proceso de la memoria real
    processName = str(processID) + "."
    processMatching = [s for s in pageTable if processName in s]
    for s in processMatching:
        i = pageTable.index(s)
        pageTable[i] = "L"

    #quitar proceso de la memoria de swap
    processName = str(processID) + "."
    processMatching = [s for s in swapTable if processName in s]
    for s in processMatching:
        i = swapTable.index(s)
        swapTable[i] = "L"

    #rquitar de CPU
    if str(CPU) == str(processID):
        CPU = "L"
        addQueueProcToCPU()

    #agregar a la cola de terminados
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
        #inicializar data
        data = ""
        data = connection.recv(256)
        ####necesidades para que funcione con el Cliente Final
        if data == "Politicas scheduling RR Memory MFU":
            print("data: " + data)
            print >>sys.stderr, 'Valid Inizialization command from', client_address
            answer = "Initializing RR with MFU"
            connection.sendall(answer)
            continue
        if data.startswith("QuantumV"):
            print("data: " + data)
            aux = data.split(" ")
            # global quantum
            quantum = float(aux[1])
            print >>sys.stderr, 'Valid Inizialization command from', client_address
            answer = "Initializing Quantum as %s" % quantum
            connection.sendall(answer)
            # setGlobals()
            continue
        if data.startswith("RealMemory"):
            print("data: " + data)
            aux = data.split(" ")
            # global realMem
            realMem = int(aux[1])
            print >>sys.stderr, 'Valid Inizialization command from', client_address
            answer = "Initializing RealMem as %s" % realMem
            connection.sendall(answer)
            # setGlobals()
            continue
        if data.startswith("SwapMemory"):
            print("data: " + data)
            aux = data.split(" ")
            # global swapMem
            swapMem = int(aux[1])
            print >>sys.stderr, 'Valid Inizialization command from', client_address
            answer = "Initializing SwapMem as %s" % swapMem
            connection.sendall(answer)
            # setGlobals()
            continue
        if data.startswith("PageSize"):
            print("data: " + data)
            aux = data.split(" ")
            # global pageSizeInKB
            pageSizeInKB = int(aux[1])
            print >>sys.stderr, 'Valid Inizialization command from', client_address
            answer = "Initializing PageSize as %s" % pageSizeInKB
            connection.sendall(answer)
            setGlobals()
            continue

        ####
        command = data
        comment = None
        parameters = []

        #obtener el comentario
        if "//" in command:
            commentSplit = data.split("//")
            command = commentSplit[0]
            comment = commentSplit[1]

        #guardar una copia del comando con sus parametros para el despliegue de la tabla
        commandFull = command

        #obtener los parametros
        if " " in  command:
            parameters = command.split(" ")
            command = parameters[0]

        #incrementar el timestamp
        incrementTimestamp(0.001)

        #inicializar direccion real
        global realAddress
        realAddress = None

        print("commando", commandFull)

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
        elif command != "End":
            print >>sys.stderr, 'Invalid command from', client_address
            answer = "Invalid command: Server terminating"
            connection.sendall(answer)
            connection.close()
            sys.exit()

        print("========================================Inicio de tabla")
        print("Commando: " + commandFull)
        print("Timestamp: " + str(timestamp))
        print("Dir. Real: " + str(realAddress))
        print("Cola de listos: "),
        print(pQueue.printQueue())
        print("CPU: " + str(CPU))
        print("Memoria Real: "),
        print(pageTable)
        print("Area de swapping:"),
        print(swapTable)
        print("Procesos Terminados:"),
        print(finished)

        # print("Stack de MFU para memoria Real:"),
        # print(mfuPageTable.printStack())
        # print("Stack de MFU para espacio de Swap:"),
        # print(mfuSwapTable.printStack())
        print("========================================Fin de tabla")
        #print(tabulate([[commandFull, timestamp, dirReal, "pQueue.printQueue()", CPU, "pageTable", "swapTable", "finished"]], headers=['Commando', 'Timestamp', 'Dir. Real', 'Cola de Listos', 'CPU', 'Memoria Real', 'Area de Swapping', 'Procesos terminados']))

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
