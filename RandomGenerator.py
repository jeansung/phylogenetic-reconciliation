# RandomGenerator.py
# Annalise Schweickart, July 2015


import random
import newickFormatReader
import DP

def findRoot(Tree):
    """This function takes in a Tree and returns a string with the name of
    the root vertex of the tree"""

    if 'pTop' in Tree:
        return Tree['pTop'][1]
    return Tree['hTop'][1] 


def orderDTL(DTL, ParasiteRoot):
    """This function takes in a DTL graph and the ParasiteRoot. It outputs a
    list, keysL, that contains tuples. Each tuple has two elements. The first
    is a mapping node of the form (p, h), where p is a parasite node and h is
    a host node. The second element is a level representing the depth of that
    mapping node within the tree."""

    keysL = []
    topNodes = []
    for key in DTL:
        if key[0] == ParasiteRoot:
            topNodes.append(key)
    for vertex in topNodes:
        keysL.extend(orderDTLRoots(DTL, vertex, 0))
    return keysL

def orderDTLRoots(DTL, vertex, level):
    """this function takes a DTL graph, one node, vertex, of the DTL graph, 
    and a level, and returns a list, keysL, that contains tuples. Each tuple
    has two elements. The first is a mapping node of the form (p, h), where p
    is a parasite node and h is a host node. The second element is a level 
    representing the depth of that mapping node within the tree. This function
    adds the input vertex to keysL and recurses on its children."""

    keysL = []
    for i in range(len(DTL[vertex]) - 1):    # loop through each event of key
        event = DTL[vertex][i]
        child1 = event[1]
        child2 = event[2]
        keysL = keysL + [(vertex, level)]
        if child1[0] != None:
            keysL.extend(orderDTLRoots(DTL, child1, level + 1))
        if child2[0] != None:
            keysL.extend(orderDTLRoots(DTL, child2, level + 1)) 
    return keysL


def sortHelper(DTL, keysL):
    """This function takes in a list orderedKeysL and deals with duplicate 
    mapping nodes that could potentially have the same level or have two 
    different levels, in which case we want to choose the highest level 
    because we are using the bottom-up approach"""
    
    uniqueKeysL = []
    for key in DTL:
        maxLevel = float("-inf")
        for element in keysL:
            if key == element[0]:
                if element[1] > maxLevel:
                    maxLevel = element[1]
        uniqueKeysL.append((key, maxLevel))
    return uniqueKeysL


def preorderDTLsort(DTL, ParasiteRoot):
    """This takes in a DTL dictionary and parasite root and returns a sorted
    list, orderedKeysL, that is ordered by level from smallest to largest,
    where level 0 is the root and the highest level has tips."""

    keysL = orderDTL(DTL, ParasiteRoot)
    uniqueKeysL = sortHelper(DTL, keysL)
    orderedKeysL = []
    levelCounter = 0
    while len(orderedKeysL) < len(uniqueKeysL):
        for mapping in uniqueKeysL:
            if mapping[-1] == levelCounter:
                orderedKeysL = orderedKeysL + [mapping]
        levelCounter += 1
    return orderedKeysL

def rootGenerator(DTL, parasiteTree):
    """Takes in a DTL graph and the parasite tree and returns a list of the 
    roots of that DTL graph"""
    parasiteRoot = findRoot(parasiteTree)
    preOrder = preorderDTLsort(DTL, parasiteRoot)
    rootList = []
    for key in preOrder:
        if key[1] == 0:
            rootList.append(key[0])
    return rootList


def randomReconGen(DTL, rootList, randomRecon):
    '''Takes as input a DTL graph, a rootList, and a growing reconciliation
    dictionary and recursively builds the reconciliation dictionary, choosing
    random events'''
    if rootList ==[]:
        return randomRecon  
    newRootL = []   
    for root in rootList:
        newChild = random.choice(DTL[root][:-1])
        print newChild
        randomRecon[root] = newChild
        if newChild[1] != (None, None) and not newChild[1] in randomRecon and\
        not newChild[1] in newRootL:
            newRootL.append(newChild[1])
        if newChild[2] != (None, None) and not newChild[2] in randomRecon and\
        not newChild[2] in newRootL:
            newRootL.append(newChild[2])
    return randomReconGen(DTL, newRootL, randomRecon)


def randomReconGenWrapper(fileName, D, T, L):
    """Takes in a file and duplication, loss and transfer costs, and calls 
    randomReconGen to build a random reconciliation"""
    hostTree, parasiteTree, phi = newickFormatReader.getInput(fileName)
    DTL, numRecon = DP.DP(hostTree, parasiteTree, phi, D, T, L)
    rootList = rootGenerator(DTL, parasiteTree)
    startRoot = random.choice(rootList)
    randomRecon = randomReconGen(DTL, [startRoot], {})
    for key in randomRecon.keys():
        randomRecon[key] = randomRecon[key][:-1]
    return randomRecon










