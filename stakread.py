#!/usr/bin/env python3

import sys
import struct

if len(sys.argv) <= 1:
    print('usage: stakread.py hypercard.stak')
    sys.exit()

class Stack:
    def __init__(self, format, script=None):
        self.format = format
        self.script = script
        self.list = None
        self.cards = []

    def __repr__(self):
        return '<Stack: %d cards>' % (len(self.cards),)

    def consistency(self):
        if not self.list:
            print('ERROR: no LIST block')
            return
        if self.list.numcards != len(self.cards):
            print('ERROR: wrong number of cards')
        for card in self.cards:
            card.consistency()
        
class BlockList:
    def __init__(self, numpages, pagesize, numcards, cardrefsize):
        self.numpages = numpages
        self.pagesize = pagesize
        self.numcards = numcards
        self.cardrefsize = cardrefsize
        self.pagerefs = []

class Card:
    def __init__(self, id, pageblockid, background, numparts, numpartconts):
        self.id = id
        self.pageblockid = pageblockid
        self.background = background
        self.numparts = numparts
        self.numpartconts = numpartconts
        self.parts = []
        self.partcontents = []
        self.script = None

    def __repr__(self):
        return '<Card %d>' % (self.id,)

    def consistency(self):
        if self.numparts != len(self.parts):
            print('ERROR: wrong number of parts')
        if self.numpartconts != len(self.partcontents):
            print('ERROR: wrong number of part contents')
    
class CardPart:
    def __init__(self, id, name, rect):
        self.id = id
        self.name = name
        self.rect = rect
        self.script = None

    def __repr__(self):
        return '<CardPart %d "%s">' % (self.id, self.name,)

def getint(dat, pos):
    val = struct.unpack('>I', dat[ pos : pos+4 ])[0]
    return val
    
def getsint(dat, pos):
    val = struct.unpack('>i', dat[ pos : pos+4 ])[0]
    return val
    
def getshort(dat, pos):
    val = struct.unpack('>H', dat[ pos : pos+2 ])[0]
    return val

def getstring(dat, pos):
    ix = pos
    while dat[ix]:
        ix += 1
    val = dat[ pos : ix ].decode('mac_roman')
    return val, ix+1

def endnulls(script):
    pos = 0
    while pos < len(script) and script[pos] == 0:
        pos += 1
    if pos > 0:
        script = script[ pos : ]
    pos = len(script)-1
    while pos > 0 and script[pos] == 0:
        pos -= 1
    if pos < len(script)-1:
        script = script[ : pos+1 ]
    return script

def decode_script(script):
    script = endnulls(script)
    if not len(script):
        return None
    script = script.decode('mac_roman').replace('\r', '\n')
    return script

def parse(filename):
    with open(filename, 'rb') as fl:
        dat = fl.read()
        
    stack = None
    pos = 0
    
    while pos < len(dat):
        bsize = getint(dat, pos+0)
        btype = dat[ pos+4 : pos+8 ].decode()
        bid = getsint(dat, pos+8)
        block = dat[ pos : pos+bsize ]
        if btype == 'STAK':
            assert stack is None
            # This must be the first block
            stack = parse_stak(block, bid)
        elif btype == 'LIST':
            stack.list = parse_list(block, bid)
        elif btype == 'CARD':
            card = parse_card(block, bid)
            stack.cards.append(card)
        else:
            #print('%s %d:' % (btype, bid,))
            pass
        pos += bsize
        
    return stack

def parse_stak(block, bid):
    format = getint(block, 16)
    script = block[ 0x600 : ]
    script = decode_script(script)
    stack = Stack(format, script)
    return stack

def parse_list(block, bid):
    numpages = getint(block, 0x10)
    pagesize = getint(block, 0x14)
    numcards = getint(block, 0x18)
    cardrefsize = getshort(block, 0x1C)
    res = BlockList(numpages, pagesize, numcards, cardrefsize)
    for ix in range(numpages):
        pos = 0x30 + 6*ix
        pbid = getint(block, pos)
        pcards = getshort(block, pos+4)
        res.pagerefs.append( (pbid, pcards) )
    return res

def parse_card(block, bid):
    pbid = getint(block, 0x20)
    background = getint(block, 0x24)
    numparts = getshort(block, 0x28)
    numpartconts = getshort(block, 0x30)
    card = Card(bid, pbid, background, numparts, numpartconts)

    pos = 0x36
    for ix in range(numparts):
        partsize = getshort(block, pos+0)
        partid = getshort(block, pos+2)
        partname, npos = getstring(block, pos+30)
        recttop = getshort(block, pos+6)
        rectleft = getshort(block, pos+8)
        rectbot = getshort(block, pos+10)
        rectright = getshort(block, pos+12)
        part = CardPart(partid, partname, (recttop, rectleft, rectbot, rectright))
        if npos < pos+partsize:
            assert(block[npos] == 0)
            script = block[ npos+1 : pos+partsize ]
            script = decode_script(script)
            part.script = script

        card.parts.append(part)
        pos += partsize

    for ix in range(numpartconts):
        partid = getshort(block, pos+0)
        pcsize = getshort(block, pos+2)
        if block[pos+4] == 0:
            partstr = block[ pos+5 : pos+4+pcsize ]
        else:
            numruns = getshort(block, pos+4) & 0x7FFF
            partstr = block[ pos+6+2*numruns : pos+4+pcsize ]
        partstr = partstr.decode('mac_roman')
        card.partcontents.append( (partid, partstr) )
        pos += (4+pcsize)

    script = block[ pos : ]
    script = decode_script(script)
    card.script = script

    return card
        
for filename in sys.argv[ 1 : ]:
    stack = parse(filename)
    stack.consistency()
    
    
