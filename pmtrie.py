#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @nullhashpixel
# based on: https://github.com/aiken-lang/merkle-patricia-forestry

# WARNING: untested and incomplete implementation

import json
from helpers import *

try:
    # optional
    from pycardano.plutus import CBORTag
    from pycardano.serialization import IndefiniteList
    from pycardano.serialization import ByteString
    from pycardano.plutus import RawPlutusData
except:
    pass

class PMtrie:
    TYPE_ROOT   = 'root'
    TYPE_BRANCH = 'branch'
    TYPE_LEAF   = 'leaf'

    def __init__(self, prefix='', hash=None):
        self.prefix = prefix
        self.hash   = hash if hash is not None else NULL_HASH
        self.size   = 0
        self.children = None
        self.key      = None
        self.value    = None 

    def get_type(self):
        if self.key is not None and self.value is not None:
            return PMtrie.TYPE_LEAF
        elif self.children is not None:
            return PMtrie.TYPE_BRANCH
        else:
            return PMtrie.TYPE_ROOT

    @staticmethod
    def FromList(l):
        t = PMtrie()
        for d in l:
            t.insert(d['key'], d['value'])
        return t

    @staticmethod
    def ComputeHash(prefix:str, value=None, root=None):

        assert (value is not None and root is None) or (value is None and root is not None)

        if value is not None:
            is_odd = len(prefix) % 2 == 1
            head   = bytes([0x00]) + nibbles(prefix[:1]) if is_odd else bytes([0xFF])
            tail   = bytes.fromhex(prefix[1:] if is_odd else prefix)
            assert len(value) == DIGEST_LENGTH
            return digest(head + tail + value)
        else:
            return digest(nibbles(prefix) + root)


    @staticmethod
    def Leaf(prefix:str, key, value):
        d_hex = hexdigest(encode_string(key))
        assert d_hex.endswith(prefix)

        leaf = PMtrie()
        leaf.hash   = PMtrie.ComputeHash(prefix, value=digest(encode_string(value)))
        leaf.prefix = prefix
        leaf.key    = encode_string(key)
        leaf.value  = encode_string(value)

        return leaf

    @staticmethod
    def Branch(prefix:str, children):
        branch = PMtrie()
        branch.prefix = prefix
        if type(children) is list:
            assert len(children) == 16
            branch.children = children
        elif type(children) is dict:
            branch.children = [children.get(x) for x in range(16)]
        else:
            raise Exception("TypeError")

        branch.size = sum([(1 if x is not None else 0) for x in branch.children])
        assert branch.size > 1

        branch.hash = PMtrie.ComputeHash(prefix, root=merkle_root(branch.children))
        return branch
    
    def replace_with(self, new):
        self.__dict__ = new.__dict__

    def insert_digest(self, value):
        if type(value) is str:
            self.insert(digest(bytes.fromhex(value)), bytes.fromhex(value))
        else:
            self.insert(digest(value), value)

    def insert(self, key, value):

        if self.get_type() == PMtrie.TYPE_ROOT:
            self.replace_with(PMtrie.Leaf(to_path(key), key, value))

        elif self.get_type() == PMtrie.TYPE_LEAF:
            assert key != self.key
            assert len(self.prefix) > 0

            new_path = to_path(key)[-len(self.prefix):]

            prefix = common_prefix(self.prefix, new_path)

            this_nibble = nibble(self.prefix[len(prefix)])
            new_nibble  = nibble(new_path[len(prefix)])

            assert this_nibble != new_nibble

            leaf_l = PMtrie.Leaf(self.prefix[len(prefix)+1:], self.key, self.value)
            leaf_r = PMtrie.Leaf(new_path[len(prefix)+1:], key, value)

            self.replace_with(PMtrie.Branch(prefix, {this_nibble: leaf_l, new_nibble: leaf_r}))
        else:

            def loop(node, path, parents):
                prefix = common_prefix(node.prefix, path) if len(node.prefix) > 0 else ''
                path   = path[len(prefix):]

                this_nibble = nibble(path[0])
                if len(prefix) < len(node.prefix):
                    new_prefix = node.prefix[len(prefix):]
                    new_nibble = nibble(new_prefix[0])

                    assert new_nibble != this_nibble

                    leaf_l   = PMtrie.Leaf(path[1:], key, value)
                    branch_r = PMtrie.Branch(node.prefix[len(prefix)+1:],  node.children)

                    node.replace_with(PMtrie.Branch(prefix, {this_nibble: leaf_l, new_nibble: branch_r}))
                    return parents

                parents.insert(0, node)

                child = node.children[this_nibble]
                if child is None:
                    node.children[this_nibble] = PMtrie.Leaf(path[1:], key, value)
                    node.hash = PMtrie.ComputeHash(node.prefix, root=merkle_root(node.children))
                    return parents

                if child.get_type() == PMtrie.TYPE_LEAF:
                    child.insert(key, value)
                    node.hash = PMtrie.ComputeHash(node.prefix, root=merkle_root(node.children))
                    return parents
                else:
                    return loop(child, path[1:], parents)

            parents = loop(self, to_path(key), [])
            for p in parents:
                p.size += 1
                if p.get_type() == PMtrie.TYPE_BRANCH:
                    p.hash = PMtrie.ComputeHash(p.prefix, root=merkle_root(p.children))
            return self

    def prove_digest(self, value):
        if type(value) is str:
            key = digest(bytes.fromhex(value))
        else:
            key = digest(value)
        return self.prove(key)

    def prove(self, key):
        return self.walk(to_path(key))

    def walk(self, path):
        if self.get_type() == PMtrie.TYPE_ROOT:
            raise Exception("can't do this")
        elif self.get_type() == PMtrie.TYPE_LEAF:
            assert path.startswith(self.prefix)
            return PMproof(to_path(self.key), self.value if path == self.prefix else None)
        else:
            assert path.startswith(self.prefix)
            skip = len(self.prefix)

            path = path[skip:]
            branch = nibble(path[0])

            child = self.children[branch]

            assert child is not None
            proof = child.walk(path[1:])

            return proof.rewind(child, skip, self.children)



    def inspect(self, level=0):
        type_symbol = {PMtrie.TYPE_ROOT: 'R', PMtrie.TYPE_BRANCH: '+', PMtrie.TYPE_LEAF: '>'}
        print(f"{' '*level}[{type_symbol[self.get_type()]}] size={self.size} {self.prefix} {decode_string(self.key)}-->{decode_string(self.value)} {'#'+self.hash.hex() if self.hash is not None else ''}")
        d_level = 4
        if self.get_type() == PMtrie.TYPE_BRANCH:
            for child in self.children:
                if child is not None:
                    child.inspect(level=level+d_level)

class PMproof:
    TYPE_LEAF = 'leaf'
    TYPE_FORK = 'fork'
    TYPE_BRANCH = 'branch'

    def __init__(self, path, value):
        self.path  = path
        self.value = value
        self.steps = []

    def rewind(self, target, skip, children):

        me = None
        nodes = []
        for i,child in enumerate(children):
            if child is not None:
                if child.hash == target.hash:
                    me = i
                else:
                    nodes.append(child)

        if me is None:
            raise Exception("target not in children")

        if (len(nodes) == 1):
            neighbor = nodes[0]
            if neighbor.get_type() == PMtrie.TYPE_LEAF:
                self.steps.insert(0, {
                    'type': PMproof.TYPE_LEAF,
                    'skip': skip,
                    'neighbor': {
                        'key': to_path(neighbor.key),
                        'value': digest(neighbor.value),
                        }
                    })
            else:
                self.steps.insert(0, {
                    'type': PMproof.TYPE_FORK,
                    'skip': skip,
                    'neighbor': {
                        'prefix': nibbles(neighbor.prefix),
                        'nibble': children.index(neighbor),
                        'root': merkle_root(neighbor.children),
                        }
                    })
        else:
            self.steps.insert(0, {
                'type': PMproof.TYPE_BRANCH,
                'skip': skip,
                'neighbors': merkle_proof(children, me),
                })

        return self

    def verify(self, including_item=True):
        if not including_item and len(self.steps) == 0:
            return NULL_HASH
        
        def loop(cursor, ix):
            step = self.steps[ix] if ix < len(self.steps) else None
            if step is None:
                if not including_item:
                    return None
                suffix = self.path[cursor:]
                assert self.value is not None
                return PMtrie.ComputeHash(suffix, value=digest(self.value))
            is_last_step = (ix + 1) >= len(self.steps) or self.steps[ix+1] is None
            next_cursor = cursor + 1 + step['skip']

            me = loop(next_cursor, ix+1)

            this_nibble = nibble(self.path[next_cursor -1 ])
            
            def root(nodes):
                prefix = self.path[cursor:next_cursor-1]
                merkle = merkle_root(sparse_vector(nodes))
                return PMtrie.ComputeHash(prefix, root=merkle)

            if step['type'] == PMproof.TYPE_BRANCH:
                def h(left, right):
                    return digest((left if left is not None else NULL_HASH) + (right if right is not None else NULL_HASH))

                lvl1, lvl2, lvl3, lvl4 = step['neighbors']
                merkle = {
                    0: h(h(h(h(me, lvl4), lvl3), lvl2), lvl1),
                    1: h(h(h(h(lvl4, me), lvl3), lvl2), lvl1),
                    2: h(h(h(lvl3, h(me, lvl4)), lvl2), lvl1),
                    3: h(h(h(lvl3, h(lvl4, me)), lvl2), lvl1),
                    4: h(h(lvl2, h(h(me, lvl4), lvl3)), lvl1),
                    5: h(h(lvl2, h(h(lvl4, me), lvl3)), lvl1),
                    6: h(h(lvl2, h(lvl3, h(me, lvl4))), lvl1),
                    7: h(h(lvl2, h(lvl3, h(lvl4, me))), lvl1),
                    8: h(lvl1, h(h(h(me, lvl4), lvl3), lvl2)),
                    9: h(lvl1, h(h(h(lvl4, me), lvl3), lvl2)),
                    10: h(lvl1, h(h(lvl3, h(me, lvl4)), lvl2)),
                    11: h(lvl1, h(h(lvl3, h(lvl4, me)), lvl2)),
                    12: h(lvl1, h(lvl2, h(h(me, lvl4), lvl3))),
                    13: h(lvl1, h(lvl2, h(h(lvl4, me), lvl3))),
                    14: h(lvl1, h(lvl2, h(lvl3, h(me, lvl4)))),
                    15: h(lvl1, h(lvl2, h(lvl3, h(lvl4, me)))),
                }[this_nibble]

                prefix = self.path[cursor:next_cursor-1]

                return PMtrie.ComputeHash(prefix, root=merkle)

            elif step['type'] == PMproof.TYPE_FORK:
                if not including_item and is_last_step:
                    return digest( bytes([step['neighbor']['nibble']]) + step['neighbor']['prefix'] + step['neighbor']['root'])

                assert step['neighbor']['nibble'] != this_nibble

                return root({this_nibble: me, step['neighbor']['nibble']: digest(step['neighbor']['prefix'] + step['neighbor']['root'])})

            elif step['type'] == PMproof.TYPE_LEAF:
                neighbor_path = step['neighbor']['key']
                assert neighbor_path[:cursor] == self.path[:cursor]

                neighbor_nibble = nibble(neighbor_path[next_cursor-1])
                assert neighbor_nibble != this_nibble

                if not including_item and is_last_step:
                    suffix = neighbor_path[cursor:]
                    return PMtrie.ComputeHash(suffix, value=step['neighbor']['value'])

                suffix = neighbor_path[next_cursor:]
                
                return root({this_nibble: me, neighbor_nibble: PMtrie.ComputeHash(suffix, value=step['neighbor']['value'])})
            else:
                return Exception("unknown proof type")
        
        return loop(0,0)


    def _serialize_step(self, step):
        if step['type'] == PMproof.TYPE_BRANCH:
            return dict(step, neighbors=''.join([x.hex() for x in step['neighbors'] if x is not None]))
        elif step['type'] == PMproof.TYPE_FORK:
            return dict(step, neighbor=dict(step['neighbor'], prefix=step['neighbor']['prefix'], root=step['neighbor']['root'].hex()))
        elif step['type'] == PMproof.TYPE_LEAF:
            return dict(step, neighbor={'key': step['neighbor']['key'], 'value': step['neighbor']['value'].hex()})

    def toJSON(self, full=False):
        if full:
            return json.dumps({'path': self.path, 'value': encode_string(self.value).hex(), 'steps':[self._serialize_step(step) for step in self.steps]})
        else:
            return json.dumps([self._serialize_step(step) for step in self.steps])

    def toList(self):
        result = []
        for step in self.steps:
            if step['type'] == PMproof.TYPE_BRANCH:
                result.append([0, step['skip'], ''.join([x.hex() for x in step['neighbors'] if x is not None])])
            elif step['type'] == PMproof.TYPE_FORK:
                result.append([1, step['skip'], step['neighbor']['prefix'].hex(), step['neighbor']['root'].hex()])
            elif step['type'] == PMproof.TYPE_LEAF:
                result.append([2, step['skip'], step['neighbor']['key'], step['neighbor']['value'].hex()])
        return result

    def toCBOR(self):
        cbor = '9f'
        for step in self.steps:
            if step['type'] == PMproof.TYPE_BRANCH:
                neighbors = ''.join([x.hex() for x in step['neighbors'] if x is not None])
                cbor += 'd8799f' + bytes([step['skip']]).hex() + '5f' + '5840' + neighbors[:128] + '5840' + neighbors[128:] + 'ffff' 
            elif step['type'] == PMproof.TYPE_FORK:
                if len(step['neighbor']['prefix']) < 16:
                    _prefix = bytes([0x40 + len(step['neighbor']['prefix'])]).hex() + step['neighbor']['prefix'].hex()
                else:
                    _prefix = '58' + bytes([len(step['neighbor']['prefix'])]).hex() + step['neighbor']['prefix'].hex()
                cbor += 'd87a9f' + bytes([step['skip']]).hex() + 'd8799f' + bytes([step['neighbor']['nibble']]).hex() + _prefix  + '5820' + step['neighbor']['root'].hex() + 'ffff'
            elif step['type'] == PMproof.TYPE_LEAF:
                cbor += 'd87b9f' + bytes([step['skip']]).hex() + '5820' + step['neighbor']['key'] + '5820' + step['neighbor']['value'].hex() + 'ff'
        cbor += 'ff'
        return cbor

    def toCBORlist(self):
        cbor = []
        for step in self.steps:
            if step['type'] == PMproof.TYPE_BRANCH:
                neighbors = ''.join([x.hex() for x in step['neighbors'] if x is not None])
                cbor.append('d8799f' + bytes([step['skip']]).hex() + '5f' + '5840' + neighbors[:128] + '5840' + neighbors[128:] + 'ffff')
            elif step['type'] == PMproof.TYPE_FORK:
                if len(step['neighbor']['prefix']) < 16:
                    _prefix = bytes([0x40 + len(step['neighbor']['prefix'])]).hex() + step['neighbor']['prefix'].hex()
                else:
                    _prefix = '58' + bytes([len(step['neighbor']['prefix'])]).hex() + step['neighbor']['prefix'].hex()
                cbor.append('d87a9f' + bytes([step['skip']]).hex() + 'd8799f' + bytes([step['neighbor']['nibble']]).hex() + _prefix  + '5820' + step['neighbor']['root'].hex() + 'ffff')
            elif step['type'] == PMproof.TYPE_LEAF:
                cbor.append('d87b9f' + bytes([step['skip']]).hex() + '5820' + step['neighbor']['key'] + '5820' + step['neighbor']['value'].hex() + 'ff')
        return cbor

    # when pycardano deserializes raw cbor, it creates byte arrays >64, so construct the object here
    def toPycardanoCBOR(self):
        cbor = []
        for step in self.steps:
            if step['type'] == PMproof.TYPE_BRANCH:
                cbor.append( CBORTag(121, IndefiniteList([ step['skip'], ByteString(bytes.fromhex(''.join([x.hex() for x in step['neighbors'] if x is not None]))) ])) )
            elif step['type'] == PMproof.TYPE_FORK:
                cbor.append( CBORTag(122, IndefiniteList([ step['skip'], CBORTag(121, IndefiniteList([ step['neighbor']['nibble'], step['neighbor']['prefix'], step['neighbor']['root']])) ] )))
            elif step['type'] == PMproof.TYPE_LEAF:
                cbor.append( CBORTag(123, IndefiniteList([ step['skip'], bytes.fromhex(step['neighbor']['key']), bytes.fromhex(step['neighbor']['value'].hex()) ])) )
        return RawPlutusData( IndefiniteList(cbor))

    @staticmethod
    def deserialize_step(d):
        if d['type'] == PMproof.TYPE_BRANCH:
            s = d['neighbors']
            neighbors = [bytes.fromhex(s[i:i+64]) for i in range(0, len(s), 64)]
            return dict(d, neighbors=neighbors)
        elif d['type'] == PMproof.TYPE_FORK:
            neighbor=d['neighbor']
            neighbor['root'] = bytes.fromhex(neighbor['root'])
            return dict(d, neighbor=neighbor)
        elif d['type'] == PMproof.TYPE_LEAF:
            neighbor=d['neighbor']
            neighbor['value'] = bytes.fromhex(neighbor['value'])
            return dict(d, neighbor=neighbor)
        return

    @staticmethod
    def fromJSON(l):
        d = json.loads(l)
        if type(d) is dict:
            p = PMproof(d['path'], bytes.fromhex(d['value']))
            p.steps = [PMproof.deserialize_step(x) for x in d['steps']]
        else:
            p = PMproof('', bytes([42]))
            p.steps = [PMproof.deserialize_step(x) for x in d]
        return p

    def inspect(self):
        print(f"<PROOF> {self.path} --> {self.value}")
        for i,step in enumerate(self.steps):
            print(f"-[{i}]: {step['type']} @{step['skip']}")


if __name__ == '__main__':
    t = PMtrie()
    t.insert('test','hello')
    t.insert('test2','world')
    t.insert('test3','world')
    t.insert('te3','wgdfgorld')
    t.insert('t','d')
    t.inspect()

    print("-"*80)
    t2 = PMtrie()
    t2.insert('apple[uid: 58]', '🍎')
    t2.insert('apricot[uid: 0]', '🤷')
    t2.inspect()
    t2.insert('plum[uid: 15492]', '🤷')
    t2.inspect()

    p = t.prove('te3')
    print(p.toJSON())
