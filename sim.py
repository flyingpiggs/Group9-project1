from __future__ import print_function
import os, copy

# Using these naming conventions: https://visualgit.readthedocs.io/en/latest/pages/naming_convention.html
# I won't retroactively apply them to the provided code though. 

# Function List:
# 1. netRead: read the benchmark file and build circuit netlist
# 2. gateCalc: function that will work on the logic of each gate
# 3. inputRead: function that will update the circuit dictionary made in netRead to hold the line values
# 4. read_faults: A function that reads information about the faults and generates a list that will be used to override the good circuit operations. 
# 5. basic_sim: the actual simulation
# 6. main: The main function

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Neatly prints the Circuit Dictionary:
def printCkt (circuit):
    print("INPUT LIST:")
    for x in circuit["INPUTS"][1]:
        print(x + "= ", end='')
        print(circuit[x])

    print("\nOUTPUT LIST:")
    for x in circuit["OUTPUTS"][1]:
        print(x + "= ", end='')
        print(circuit[x])

    print("\nGATE list:")
    for x in circuit["GATES"][1]:
        print(x + "= ", end='')
        print(circuit[x])
    print()


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Reading in the Circuit gate-level netlist file:
def netRead(netName):
    # Opening the netlist file:
    netFile = open(netName, "r")

    # temporary variables
    inputs = []     # array of the input wires
    outputs = []    # array of the output wires
    gates = []      # array of the gate list
    inputBits = 0   # the number of inputs needed in this given circuit


    # main variable to hold the circuit netlist, this is a dictionary in Python, where:
    # key = wire name; value = a list of attributes of the wire
    circuit = {}

    # Reading in the netlist file line by line
    for line in netFile:

        # NOT Reading any empty lines
        if (line == "\n"):
            continue

        # Removing spaces and newlines
        line = line.replace(" ","")
        line = line.replace("\n","")

        # NOT Reading any comments
        if (line[0] == "#"):
            continue

        # @ Here it should just be in one of these formats:
        # INPUT(x)
        # OUTPUT(y)
        # z=LOGIC(a,b,c,...)

        # Read a INPUT wire and add to circuit:
        if (line[0:5] == "INPUT"):
            # Removing everything but the line variable name
            line = line.replace("INPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            # Format the variable name to wire_*VAR_NAME*
            line = "wire_" + line

            # Error detection: line being made already exists
            if line in circuit:
                msg = "NETLIST ERROR: INPUT LINE \"" + line + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
                print(msg + "\n")
                return msg

            # Appending to the inputs array and update the inputBits
            inputs.append(line)

            # add this wire as an entry to the circuit dictionary
            circuit[line] = ["INPUT", line, False, 'U']

            inputBits += 1
            print(line)
            print(circuit[line])
            continue

        # Read an OUTPUT wire and add to the output array list
        # Note that the same wire should also appear somewhere else as a GATE output
        if line[0:6] == "OUTPUT":
            # Removing everything but the numbers
            line = line.replace("OUTPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            # Appending to the output array
            outputs.append("wire_" + line)
            continue

        # Read a gate output wire, and add to the circuit dictionary
        lineSpliced = line.split("=") # splicing the line at the equals sign to get the gate output wire
        gateOut = "wire_" + lineSpliced[0]

        # Error detection: line being made already exists
        if gateOut in circuit:
            msg = "NETLIST ERROR: GATE OUTPUT LINE \"" + gateOut + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
            print(msg+"\n")
            return msg

        # Appending the dest name to the gate list
        gates.append(gateOut)

        lineSpliced = lineSpliced[1].split("(") # splicing the line again at the "("  to get the gate logic
        logic = lineSpliced[0].upper()


        lineSpliced[1] = lineSpliced[1].replace(")", "")
        terms = lineSpliced[1].split(",")  # Splicing the the line again at each comma to the get the gate terminals
        # Turning each term into an integer before putting it into the circuit dictionary
        terms = ["wire_" + x for x in terms]

        # add the gate output wire to the circuit dictionary with the dest as the key
        circuit[gateOut] = [logic, terms, False, 'U']
        print(gateOut)
        print(circuit[gateOut])

    # now after each wire is built into the circuit dictionary,
    # add a few more non-wire items: input width, input array, output array, gate list
    # for convenience
    
    circuit["INPUT_WIDTH"] = ["input width:", inputBits]
    circuit["INPUTS"] = ["Input list", inputs]
    circuit["OUTPUTS"] = ["Output list", outputs]
    circuit["GATES"] = ["Gate list", gates]

    print("\n bookkeeping items in circuit: \n")
    print(circuit["INPUT_WIDTH"])
    print(circuit["INPUTS"])
    print(circuit["OUTPUTS"])
    print(circuit["GATES"])


    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: calculates the output value for each logic gate
# if faults == None, then we're running the non-faulty circuit
def gateCalc(circuit, node, faults):
    
    # terminal will contain all the input wires of this logic gate (node)
    terminals = list(circuit[node][1])  

    # If the node is an Inverter gate output, solve and return the output
    if circuit[node][0] == "NOT":
        if circuit[terminals[0]][3] == '0':
            circuit[node][3] = '1'
        elif circuit[terminals[0]][3] == '1':
            circuit[node][3] = '0'
        elif circuit[terminals[0]][3] == "U":
            circuit[node][3] = "U"
        else:  # Should not be able to come here
            return -1
        return circuit

# Comment blocks for tomorrow regarding how to use the new dictionary I created

# First of all, does python have the same feature as Javascript where if I don't have an input for some variable,
# it's just set as None? I need to double check this, and if not, I need to make sure I change the function calls where needed
# I also need to make sure that I'm making a deep copy of circuit so that I have a faulty circuit simulation and a good circuit simulation

# I need to iterate through the faults[wireName]["terminals"] and find which index it's at so that I can use the index
# to access the correct index of ["value"] to block the signal from the good circuit and replace it with the fault.
# I need to make sure I save the signal from the good circuit though because I won't know whether or not there are fan-outs
# within the scope of this code so I have to save the value so that I can restore it after the faulty output is calculated.

# Things are easier when the fault is at an output wire since I know that the index for ["value"] must be 0
# and I can just overwrite the value without having to worry about fan-outs since it'll be handled by whatever I do 
# to deal with the issue mentioned in the previous comment block.

    # If the node is an AND gate output, solve and return the output
    elif circuit[node][0] == "AND":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a flag that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 at any input terminal, AND output is 0. If there is an unknown terminal, mark the flag
        # Otherwise, keep it at 1
        for term in terminals:  
            if circuit[term][3] == '0':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        return circuit

    # If the node is a NAND gate output, solve and return the output
    elif circuit[node][0] == "NAND":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 terminal, NAND changes the output to 1. If there is an unknown terminal, it
        # changes to "U" Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '0':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
                break

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        return circuit

    # If the node is an OR gate output, solve and return the output
    elif circuit[node][0] == "OR":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, OR changes the output to 1. Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        return circuit

    # If the node is an NOR gate output, solve and return the output
    if circuit[node][0] == "NOR":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, NOR changes the output to 0. Otherwise, keep it at 1
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        return circuit

    # If the node is an XOR gate output, solve and return the output
    if circuit[node][0] == "XOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there are an odd number of terminals, XOR outputs 1. Otherwise, it should output 0
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        return circuit

    # If the node is an XNOR gate output, solve and return the output
    elif circuit[node][0] == "XNOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there is a single 1 terminal, XNOR outputs 0. Otherwise, it outputs 1
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                return circuit

        # check how many 1's we counted

# 	!!!!!!!!!! PRETTY SURE THERE'S A BUG HERE  !!!!!!!!!!!!!
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        return circuit

    # Error detection... should not be able to get at this point
    return circuit[node][0]

# Author: Peter
# Function purpose:
#	Note: Dictionary is referring to the python dictionary, not a dictionary we look up words in. Also, list will refer
#		to the programming list since python doesn't technically have arrays. 

#	This function is meant to read in information about the faults, then produce a dictionary that will have the necessary 
#	information we need during the circuit simulation to override the good circuit. The keys into this dictionary should 
#	correspond to the wire that is used to identify nodes in the circuit simulation.

#	Each member of this dictionary will be its own dictionary with the following key/value pairings:
#	value : whatever value this fault will be stuck at, will be '0' or '1'
#	terminals : refers to the input wire of a logic gate, will be a string of some sort
#	Note: The wires in the given code follow the format "wire_NAME" where NAME is whatever it was in the benchmark file

# Parameters: 
# 1.  faultInfo
#	A text file that lists the faults that will be present in the circuit simulation

#	Note: There's an assumption that the faults in this list will be actual wires in the associated benchmark file
#	i.e. I'm not going to bother doing any input sanitation, nor should there be comments or anything like that in the fault file.
#	Also, I'm hoping that no one decides to name any of the inputs, outputs, or logic gates as SA-0 SA-1 because this code would 
#	bug, but let's see what happens...
#	Lastly, the expected format for faults in this text file will be something similar to as follows:
#		If just a wire is faulty, then it should be something like "A-SA-0"
#		If the input to a gate is fault, then if the output wire is called K and input wire is called g, 
#		then the fault should appear as "K-IN-g-SA-0"

# Returns: faults, a dictionary of the faults 

def read_faults( faultInfo ):

    faults = {} 
    for info in faultInfo:
        splitString = info.split("-")
        wire = "wire_" + splitString[0]

        if ( wire in faults ):
            if ( "wire_" + splitString[2] in faults[wire]["terminals"] ):
                print( "There's was a conflict during fault assignment of input wires for a gate, ending read_faults()..." )
                return -1
            elif ( faults[wire]["terminals"] == None ):
                print( "There's was a conflict during fault assignment of a line, ending read_faults()..." )
                return -2
            if ( "SA-0" in info):
                faults[wire]["value"].append( "0" )
            elif( "SA-1" in info ):
                faults[wire]["value"].append( "1" )
            faults[wire]["terminals"].append( "wire_" + splitString[2] )
            continue
        
        fault = {}
        if ( "IN" in info ):
#	These values need to be lists in this case to deal with different input wires to the same logic gate
            if ( "SA-0" in info ):
                fault["value"] = [ "0" ]
            elif( "SA-1" in info ):
                fault["value"] = [ "1" ] 
            fault["terminals"] = [ "wire_" + splitString[2] ] 
#	The 2 is due to the expected format of a fault when it's the input wire to a logic gate
        else:
            fault["terminals"] = None
            if ( "SA-0" in info ):
                fault["value"] = [ "0" ]
            elif( "SA-1" in info ):
                fault["value"] = [ "1" ]
#	value in this case doesn't really have to be a list since we shouldn't have duplicates, but I wanted to be consistent
        fault[wire] = fault
#	End of the loop
     	
    return faults 

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Updating the circuit dictionary with the input line, and also resetting the gates and output lines
def inputRead(circuit, line):
    # Checking if input bits are enough for the circuit
    if len(line) < circuit["INPUT_WIDTH"][1]:
        return -1

    # Getting the proper number of bits:
    line = line[(len(line) - circuit["INPUT_WIDTH"][1]):(len(line))]

    # Adding the inputs to the dictionary
    # Since the for loop will start at the most significant bit, we start at input width N
    i = circuit["INPUT_WIDTH"][1] - 1
    inputs = list(circuit["INPUTS"][1])
    # dictionary item: [(bool) If accessed, (int) the value of each line, (int) layer number, (str) origin of U value]
    for bitVal in line:
        bitVal = bitVal.upper() # in the case user input lower-case u
        circuit[inputs[i]][3] = bitVal # put the bit value as the line value
        circuit[inputs[i]][2] = True  # and make it so that this line is accessed

        # In case the input has an invalid character (i.e. not "0", "1" or "U"), return an error flag
        if bitVal != "0" and bitVal != "1" and bitVal != "U":
            return -2
        i -= 1 # continuing the increments

    return circuit

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: the actual simulation #
def basic_sim( circuit, faults, isRunningFaults ):
    # QUEUE and DEQUEUE
    # Creating a queue, using a list, containing all of the gates in the circuit
    queue = list(circuit["GATES"][1])
    i = 1

    if ( isRunningFaults ):
        print( "\nRunning the faulty circuit..." )

    while True:
        i -= 1
        # If there's no more things in queue, done
        if len(queue) == 0:
            break

        # Remove the first element of the queue and assign it to a variable for us to use
        curr = queue[0]
        queue.remove(curr)

        # initialize a flag, used to check if every terminal has been accessed
        term_has_value = True

        # Check if the terminals have been accessed
        for term in circuit[curr][1]:
            if not circuit[term][2]:
                term_has_value = False
                break

        if term_has_value:
            circuit[curr][2] = True
            if ( isRunningFaults ): 
                circuit = gateCalc( circuit, curr, faults )
            else:
                circuit = gateCalc( circuit, curr, None )

            # ERROR Detection if LOGIC does not exist
            if isinstance(circuit, str):
                print(circuit)
                return circuit

            print("Progress: updating " + curr + " = " + circuit[curr][3] + " as the output of " + circuit[curr][0] + " for:")
            for term in circuit[curr][1]:
                print(term + " = " + circuit[term][3])
            print("\nPress Enter to Continue...")
            input()

        else:
            # If the terminals have not been accessed yet, append the current node at the end of the queue
            queue.append(curr)
    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Main Function
def main():
    # **************************************************************************************************************** #
    # NOTE: UI code; Does not contain anything about the actual simulation

    # Used for file access
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

    print("Circuit Simulator:")

    # Select circuit benchmark file, default is circuit.bench
    while True:
        cktFile = "circuit.bench"   
        print("\n Read circuit benchmark file: use " + cktFile + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            cktFile = os.path.join(script_dir, userInput)
            if not os.path.isfile(cktFile):
                print("File does not exist. \n")
            else:
                break

    print("\n Reading " + cktFile + " ... \n")
    circuit = netRead(cktFile)
    print("\n Finished processing benchmark file and built netlist dictionary: \n")
    # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
    # printCkt(circuit)
    print(circuit)

    # keep an initial (unassigned any value) copy of the circuit for an easy reset
    newCircuit = circuit
    faultyCircuit = copy.deepcopy( circuit )
    newFaultyCircuit = faultyCircuit

    # Select input file, default is input.txt
    while True:
        inputName = "input.txt"
        print("\n Read input vector file: use " + inputName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":

            break
        else:
            inputName = os.path.join(script_dir, userInput)
            if not os.path.isfile(inputName):
                print("File does not exist. \n")
            else:
                break

    # Select the faults file
    while True:
        faultsName = "faults.txt"
        print("\n Read fault file: use " + inputName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":

            break
        else:
            faultsName = os.path.join(script_dir, userInput)
            if not os.path.isfile( faultsName ):
                print("File does not exist. \n")
            else:
                break
    
    print( "\nReading the faults file..." )
    faultsFile = open( faultsName, "r" )
    faults = read_faults( faultsFile )


    # Select output file, default is output.txt
    while True:
        outputName = "output.txt"
        print("\n Write output file: use " + outputName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            outputName = os.path.join(script_dir, userInput)
            break

    # Note: UI code;
    # **************************************************************************************************************** #

    print("\n *** Simulating the" + inputName + " file and will output in" + outputName + "*** \n")
    inputFile = open(inputName, "r")
    outputFile = open(outputName, "w")
    faultyOutputFile = open( "faulty_" + outputName, "w" )

    # Runs the simulator for each line of the input file
    for line in inputFile:
        # Initializing output variable each input line
        output = ""
        faultyOutput = ""

        # Do nothing else if empty lines, ...
        if (line == "\n"):
            continue
        # ... or any comments
        if (line[0] == "#"):
            continue

        # Removing the the newlines at the end and then output it to the txt file
        line = line.replace("\n", "")
        outputFile.write(line)
        faultyOutputFile.write( line )

        # Removing spaces
        line = line.replace(" ", "")
        
        print("\n before processing circuit dictionary...")
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        # printCkt(circuit)
        print(circuit)
        print("\n ---> Now ready to simulate INPUT = " + line)
        circuit = inputRead(circuit, line)
        faultyCircuit = inputRead( faultyCircuit, line ) 
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        # printCkt(circuit)
        print(circuit)


        if circuit == -1:
            print("INPUT ERROR: INSUFFICIENT BITS")
            outputFile.write(" -> INPUT ERROR: INSUFFICIENT BITS" + "\n")
            faultyOutputFile.write( " -> INPUT ERROR: INSUFFICIENT BITS" + "\n" )
            # After each input line is finished, reset the netList
            circuit = newCircuit
            faultyCircuit = newFaultyCircuit
            print("...move on to next input\n")
            continue
        elif circuit == -2:
            print("INPUT ERROR: INVALID INPUT VALUE/S")
            outputFile.write(" -> INPUT ERROR: INVALID INPUT VALUE/S" + "\n")
            faultyOutputFile.write( " -> INPUT ERROR: INVALID INPUT VALUE/S" + "\n" )
            # After each input line is finished, reset the netList
            circuit = newCircuit
            faultyCircuit = newFaultyCircuit
            print("...move on to next input\n")
            continue


        circuit = basic_sim( circuit, None, False )
        faultCircuit = basic_sim( faultyCircuit, faults, True )
        print("\n *** Finished simulation - resulting circuit: \n")
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        # printCkt(circuit)
        print(circuit)


        for y in circuit["OUTPUTS"][1]:
            if not circuit[y][2]:
                output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                faultyOutput = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                break
            output = str(circuit[y][3]) + output
            faultyOutput = str(circuit[y][3]) + faultyOutput

        print("\n *** Summary of simulation: ")
        print(line + " -> " + output + " written into output file. \n")
        outputFile.write( " -> " + output + "\n" )
        faultyOutputFile.write( " -> " + faultyOutput + "\n" )

        # After each input line is finished, reset the circuit
        print("\n *** Now resetting circuit back to unknowns... \n")
       
        for key in circuit:
            if (key[0:5]=="wire_"):
                circuit[key][2] = False
                circuit[key][3] = 'U'
                faultyCircuit[key][2] = False
                faultyCircuit[key][3] = 'U'

        print("\n circuit after resetting: \n")
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        # printCkt(circuit)
        print(circuit)

        print("\n*******************\n")
        
    outputFile.close
    faultyOutputFile.close
    #exit()


if __name__ == "__main__":
    main()

