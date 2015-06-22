

from rasmus import treelib1, util
import copy
import sys
import MasterReconciliation
import newickFormatReader

def convert(fileName, HostOrder):

    f = open(fileName, 'r')
    contents = f.read()
    host, paras, phi = host, paras, phi = newickFormatReader.getInput(fileName)
    hostRoot = MasterReconciliation.findRoot(host)
    f.close()
    H,P,phi = contents.split(";")
    P = P.strip()
    H = H.strip()
    H = H + ';'
    host = treelib1.parse_newick(H, HostOrder)
  
    # for key in HostOrder:
    #     H = H.replace(str(key), str(key) + ':' + str(HostOrder[key]))
    f = open(fileName[:-7]+".stree", 'w')
    treelib1.write_newick(host, f, root_data = True)
    f.close()
    f = open(fileName[:-7] + '.tree', 'w')
    f.write(P + ";")
    f.close