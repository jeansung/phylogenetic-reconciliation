#newickToVis.py
#July 2015
#Carter Slocum

#File contains function that creates separate newick files for the parasite tree and the ultra-metric 
#host tree.

from rasmus import treelib1, util
import copy
import sys
import MasterReconciliation
import newickFormatReader

def convert(fileName, HostOrder, n, partoo):
    """takes name of origional file and the dictionary of host tree branch lengths
    and creates files for the host + parasite trees"""
    f = open(fileName, 'r')
    contents = f.read()
    host, paras, phi = newickFormatReader.getInput(fileName)
    hostRoot = MasterReconciliation.findRoot(host)
    f.close()
    H,P,phi = contents.split(";")
    P = P.strip()
    print P
    H = H.strip()
    H = H + ';'
    host = treelib1.parse_newick(H, HostOrder)
    for key in HostOrder:
        H = H.replace(str(key), str(key) + ':' + str(HostOrder[key]))
    f = open(fileName[:-7]+ str(n) +".stree", 'w')
    treelib1.write_newick(host, f, root_data = True)
    f.close()
    if partoo:
        f = open(fileName[:-7] + '.tree', 'w')
        f.write(P + ";")
        f.close