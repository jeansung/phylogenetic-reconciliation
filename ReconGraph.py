import Queue
import random
import copy
import operator
import itertools as it
from DistanceFunction import DistanceFunction, NDistanceFunction
from DistanceFunction import SparseNDistanceFunction

flatten = lambda l: reduce(operator.add, l)

MAP_NODE      = 'map-node'
COSPECIATION  = 'S'
LEAF_PAIR     = 'C'
TRANSFER      = 'T'
DUPLICATION   = 'D'
LOSS          = 'L'

NO_CHILD = (None, None)

class Node(object):
    def __init__(self, ty, mapping = None):
        self.children = []
        self.parents = []
        self.ty = ty
        self.mapping = mapping
    def __repr__(self):
        return '<Node type: %s, mapping: %s, #child: %d, #parent: %d>' % \
                (self.ty, self.mapping, len(self.children), len(self.parents))
    def isLeaf(self):
        return len(self.children) == 0
    def isRoot(self):
        return len(self.parents) == 0
    def otherChild(self, child):
        ''' Given a child, returns a child of this node which is not that child.
        Will return None if there is no such other child.
        Uses object id() equality'''
        for c in self.children:
            if not c is child:
                return c
        return None
    def __eq__(self, other):
        if self.mapping:
            return self.mapping == other.mapping
        else:
            if self.ty != other.ty:
                return False
            if self.parents != other.parents:
                return False
            return set(self.children) == set(other.children)

class ReconGraph(object):
    def __init__(self, map_node_map):
        # Map mappings (parasite, host) to nodes
        self.map_nodes = {}
        def get_or_make_map_node(mapping):
            if mapping not in self.map_nodes:
                self.map_nodes[mapping] = Node(MAP_NODE, mapping)
            return self.map_nodes[mapping]
        for mapping in map_node_map:
            event_children = map_node_map[mapping][:-1]
            for ty, child1mapping, child2mapping, _ in event_children:
                parent_map_node = get_or_make_map_node(mapping)
                event_node = Node(ty)
                if child1mapping != NO_CHILD:
                    child1 = get_or_make_map_node(child1mapping)
                    event_node.children.append(child1)
                    child1.parents.append(event_node)
                if child2mapping != NO_CHILD:
                    child2 = get_or_make_map_node(child2mapping)
                    event_node.children.append(child2)
                    child2.parents.append(event_node)
                parent_map_node.children.append(event_node)
                event_node.parents.append(parent_map_node)
        self.map_node_map = map_node_map
        self.roots = [self.map_nodes[root] for root in self.get_root_mappings()]
    def get_root_mappings(self):
        G = self.map_node_map
        childrenMaps = flatten(flatten([[children[1:-1] for children in vals if type(children) == type([])] for vals in G.values()]))
        return list(set(G.keys()) - set(childrenMaps))
    def postorder(self):
        return ReconGraphPostorder(self)
    def preorder(self):
        return reversed(list(self.postorder()))

class ReconGraphPostorder(object):
    def __init__(self, G):
        self.G = G
        self.q = G.roots[:]
        self.visited = set([])
    def __iter__(self):
        return self
    def next(self):
        if len(self.q) == 0:
            raise StopIteration
        nxt = self.q.pop()
        new_children = len(filter(lambda c: c not in self.visited, nxt.children))
        if new_children == 0:
            self.visited.add(nxt)
            return nxt
        else:
            self.q.append(nxt)
            for child in nxt.children:
                if child not in self.visited:
                    self.q.append(child)
            return self.next()

def _subcounts(graph, template_event_set):
    table = {}
    for n in graph.postorder():
        if n.isLeaf():
            table[n] = DistanceFunction.kronicker(-1)
        elif n.ty == MAP_NODE:
            table[n] = reduce(lambda x, y: x.sum(y), \
                                       [table[c] for c in n.children])
        else:
            shift_amount = 1 if n not in template_event_set else -1
            table[n] = reduce(lambda x, y: x.convolve(y), \
                                       [table[c] for c in n.children])
            table[n] = table[n].shift(shift_amount)
    return table

def _supercounts(graph, template_event_set, subcount_table):
    table = {}
    for n in graph.preorder():
        if n.isRoot():
            table[n] = DistanceFunction.kronicker(0)
        elif n.ty == MAP_NODE:
            def process_parent(event_parent):
                shift_amount = 1 if event_parent not in template_event_set else -1
                parent_super = table[event_parent]
                otherChild = event_parent.otherChild(n)
                convolved = parent_super.convolve(subcount_table[otherChild]) \
                                if otherChild \
                                else parent_super
                return convolved.shift(shift_amount)
            sup_count = reduce(lambda x, y: x.sum(y), map(process_parent, n.parents))
            table[n] = sup_count
        else:
            shift_amount = 1 if n not in template_event_set else -1
            # Event nodes inherit their single parent's super-count.
            # Shallow copy is same because we don't mutatate Fn's
            table[n] = table[n.parents[0]]
    return table

def _counts(graph, template_event_set, subcount_table, supercount_table):
    count_table = {}
    offset = len(template_event_set)
    for n in graph.postorder():
        count_table[n] = \
                subcount_table[n].convolve(supercount_table[n]).shift(offset)
    return count_table

def counts(graph, template_event_set):
    subcount_table = _subcounts(graph, template_event_set)
    supercount_table = _supercounts(graph, template_event_set, subcount_table)
    return subcount_table, \
            supercount_table, \
            _counts(graph, template_event_set, subcount_table, supercount_table)

def _subcounts_n(graph, template_event_set_s, fn_class):
    table = {}
    for n in graph.postorder():
        if n.isLeaf():
            table[n] = fn_class.kronicker(
                    tuple(-1 for i in xrange(len(template_event_set_s))))
        elif n.ty == MAP_NODE:
            table[n] = reduce(lambda x, y: x.sum(y), \
                                       [table[c] for c in n.children])
        else:
            shift_amount = [1 if n not in template_event_set else -1 for \
                    template_event_set in template_event_set_s]
            table[n] = reduce(lambda x, y: x.convolve(y), \
                                       [table[c] for c in n.children])
            table[n] = table[n].shift(shift_amount)
    return table

def _supercounts_n(graph, template_event_set_s, subcount_table, fn_class):
    table = {}
    for n in graph.preorder():
        if n.isRoot():
            table[n] = fn_class.kronicker(
                    tuple(0 for i in xrange(len(template_event_set_s))))
        elif n.ty == MAP_NODE:
            def process_parent(event_parent):
                shift_amount = [1 if event_parent not in template_event_set else -1 for \
                        template_event_set in template_event_set_s]
                parent_super = table[event_parent]
                otherChild = event_parent.otherChild(n)
                convolved = parent_super.convolve(subcount_table[otherChild]) \
                                if otherChild \
                                else parent_super
                return convolved.shift(shift_amount)
            sup_count = reduce(lambda x, y: x.sum(y), map(process_parent, n.parents))
            table[n] = sup_count
        else:
            shift_amount = [1 if n not in template_event_set else -1 for \
                    template_event_set in template_event_set_s]
            # Event nodes inherit their single parent's super-count.
            # Shallow copy is same because we don't mutatate Fn's
            table[n] = table[n.parents[0]]
    return table

def _counts_n(graph, template_event_set_s, subcount_table, supercount_table):
    count_table = {}
    offsets = [len(template_event_set) for template_event_set in template_event_set_s]
    for n in graph.postorder():
        count_table[n] = \
                subcount_table[n].convolve(supercount_table[n]).shift(offsets)
    return count_table

def counts_n(graph, template_event_set_s, fn_class):
    subcount_table = _subcounts_n(graph, template_event_set_s, fn_class)
    supercount_table = _supercounts_n(graph, template_event_set_s, subcount_table, fn_class)
    return subcount_table, \
            supercount_table, \
            _counts_n(graph, template_event_set_s, subcount_table, supercount_table)

def sparse_counts_n(graph, template_event_set_s):
    return counts_n(graph, template_event_set_s, SparseNDistanceFunction)

def dense_counts_n(graph, template_event_set_s):
    return counts_n(graph, template_event_set_s, NDistanceFunction)


def get_template(graph):
    events = set([])
    stack = [random.choice(graph.roots)]
    while len(stack) > 0:
        n = stack.pop()
        if n.ty != MAP_NODE:
            events.add(n)
            for c in n.children:
                stack.append(c)
        else:
            stack.append(random.choice(n.children))
    return events

f = open('t.g')
G = eval(f.read())
f.close()

GG = ReconGraph(G)

random.seed(0)
template = get_template(GG)
template2 = get_template(GG)
template3 = get_template(GG)

sub_cs, sup_cs, cs = counts(GG, template)
r = GG.roots[0]

# sub_cs2, sup_cs2, cs2 = counts_n(GG, [template, template2])
sub_cs2, sup_cs2, cs2 = sparse_counts_n(GG, [template, template2])
#sub_cs3, sup_cs3, cs3 = dense_counts_n(GG, [template, template2])
sub_cs4, sup_cs4, cs4 = sparse_counts_n(GG, [template, template2, template3])
