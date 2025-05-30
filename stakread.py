#!/usr/bin/env python3

"""stakread.py: Minimal HyperCard stack parser
- by Andrew Plotkin
- http://github.com/erkyrath/mystextract

This extracts the card and HyperTalk data from a HyperCard stack.
It is *not* complete; I am only interested in the HyperText text, so
that's all I did.

Usage:
  stakread.py [ -o OUTFILE ] hypercard.stak

If -o is given, this writes a human-readable overview of the stack and
its cards and scripts to the given file. (Or stdout if you do "-o -".)

Without -o, this just parses the stack and exits. You could use this to
inspect the stack at the Python prompt:

  python3 -i stakread.py hypercard.stak
  >>> stack
  <Stack: 30 cards, 1 backgrounds>
  >>> print(len(stack.script))
  4587

The HyperCard format is described here:
  https://hypercard.org/hypercard_file_format_pierre/
  https://github.com/PierreLorenzi/HyperCardPreview/blob/master/StackFormat.md

A much more complete HyperCard stack extractor is here:
  https://github.com/uliwitness/stackimport

This script is in the public domain.
"""

import sys
import struct
import optparse

popt = optparse.OptionParser(usage='stakread.py [ -o OUTFILE ] STACK')

popt.add_option('-o', '--output',
                action='store', dest='outfile')

(opts, args) = popt.parse_args()


class Stack:
    """Stack: represents an entire HyperCard stack.
    """
    def __init__(self, format, numbackgrounds, numcards, createversion, modversion, cardrect, pixsize, script=None):
        self.format = format
        self.numbackgrounds = numbackgrounds
        self.numcards = numcards
        self.createversion = createversion
        self.modversion = modversion
        self.cardrect = cardrect
        self.pixsize = pixsize
        self.script = script
        self.list = None
        self.cards = []
        self.backgrounds = []
        self.cardmap = {}
        self.backgroundmap = {}

    def __repr__(self):
        return '<Stack: %d cards, %d backgrounds>' % (len(self.cards), len(self.backgrounds),)

    def finalize(self):
        """We call this after loading everything. Set up handy maps
        and check for errors.
        """
        for card in self.cards:
            self.cardmap[card.id] = card
        for bkgd in self.backgrounds:
            self.backgroundmap[bkgd.id] = bkgd
            
        self.consistency()

    def consistency(self):
        """Consistency check. This shouldn't show any errors; if it does,
        I made a mistake somewhere.
        """
        if not self.list:
            print('ERROR: no LIST block')
            return
        if self.numcards != len(self.cards):
            print('ERROR: wrong number of cards')
        if self.list.numcards != len(self.cards):
            print('ERROR: wrong number of cards')
        if self.numbackgrounds != len(self.backgrounds):
            print('ERROR: wrong number of backgrounds')
        for card in self.cards:
            card.consistency()

    def dump(self, outfl):
        """Write the contents of the stack to outfl.
        """
        outfl.write('Stack (%d cards, %d backgrounds)\n' % (len(self.cards), len(self.backgrounds),))
        
        if self.script:
            outfl.write('\n')
            print_script(self.script, outfl, indent=2)
            outfl.write('\n')

        for card in self.cards:
            card.dump(outfl)
        
        for bkgd in self.backgrounds:
            bkgd.dump(outfl)
        
class BlockList:
    """BlockList: a block list block (the LIST type).
    """
    def __init__(self, numpages, pagesize, numcards, cardrefsize):
        self.numpages = numpages
        self.pagesize = pagesize
        self.numcards = numcards
        self.cardrefsize = cardrefsize
        self.pagerefs = []

class Card:
    """Card: represents one card in a stack.
    """
    def __init__(self, id, pageblockid, background, numparts, numpartconts):
        self.id = id
        self.pageblockid = pageblockid
        self.background = background
        self.numparts = numparts
        self.numpartconts = numpartconts
        self.parts = []
        self.partcontents = []
        self.name = None
        self.script = None

    def __repr__(self):
        return '<Card %d "%s">' % (self.id, self.name,)

    def consistency(self):
        if self.numparts != len(self.parts):
            print('ERROR: wrong number of parts')
        if self.numpartconts != len(self.partcontents):
            print('ERROR: wrong number of part contents')
    
    def dump(self, outfl):
        outfl.write('  * Card %d "%s" (%d parts)\n' % (self.id, self.name, len(self.parts),))
        
        if self.script:
            outfl.write('\n')
            print_script(self.script, outfl, indent=4)
            outfl.write('\n')
            
        for part in self.parts:
            part.dump(self.id, outfl)

class Background:
    """Background: a background block.
    """
    def __init__(self, id, numparts, numpartconts):
        self.id = id
        self.numparts = numparts
        self.numpartconts = numpartconts
        self.parts = []
        self.partcontents = []
        self.name = None
        self.script = None

    def __repr__(self):
        return '<Background %d "%s">' % (self.id, self.name,)

    def consistency(self):
        if self.numparts != len(self.parts):
            print('ERROR: wrong number of parts')
        if self.numpartconts != len(self.partcontents):
            print('ERROR: wrong number of part contents')
    
    def dump(self, outfl):
        outfl.write('  * Background %d "%s" (%d parts)\n' % (self.id, self.name, len(self.parts),))
        
        if self.script:
            outfl.write('\n')
            print_script(self.script, outfl, indent=4)
            outfl.write('\n')
            
        for part in self.parts:
            part.dump(self.id, outfl)

class CardPart:
    """CardPart: one element of a Card or Background. Buttons are the most
    familiar CardPart.
    """
    def __init__(self, id, name, rect):
        self.id = id
        self.name = name
        self.rect = rect
        self.script = None

    def __repr__(self):
        return '<CardPart %d "%s">' % (self.id, self.name,)

    def dump(self, cardid, outfl):
        outfl.write('    * Part %d:%d "%s"\n' % (cardid, self.id, self.name,))
        if self.script:
            print_script(self.script, outfl, indent=6)

class Size:
    """Size: a (width, height) pair.
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __repr__(self):
        return '<Size width=%d height=%d>' % (self.width, self.height,)
    
class Rect:
    """Rect: a (top, left, bottom, right) tuple.
    """
    def __init__(self, top, left, bottom, right):
        self.top = top
        self.left = left
        self.bottom = bottom
        self.right = right

    def __repr__(self):
        return '<Rect top=%d left=%d bottom=%d right=%d>' % (self.top, self.left, self.bottom, self.right,)

# Utility functions to pull various types out of binary data.
    
def getint(dat, pos):
    val = struct.unpack('>I', dat[ pos : pos+4 ])[0]
    return val
    
def getsignint(dat, pos):
    val = struct.unpack('>i', dat[ pos : pos+4 ])[0]
    return val
    
def getshort(dat, pos):
    val = struct.unpack('>H', dat[ pos : pos+2 ])[0]
    return val

def getsignshort(dat, pos):
    val = struct.unpack('>h', dat[ pos : pos+2 ])[0]
    return val

def getstring(dat, pos):
    ix = pos
    while ix < len(dat) and dat[ix]:
        ix += 1
    val = dat[ pos : ix ].decode('mac_roman')
    return val, ix+1

def getversion(dat, pos):
    statemap = { 0x20:'dev', 0x40:'alpha', 0x60:'beta', 0x80:'final' }
    major = dat[pos]
    minor = (dat[pos+1] >> 4) & 0x0F
    patch = (dat[pos+1]) & 0x0F
    state = dat[pos+2]
    state = statemap.get(state, hex(state))
    release = dat[pos+3]
    return '%d.%d.%d-%s-%d' % (major, minor, patch, state, release,)

def getrectangle(dat, pos):
    recttop = getshort(dat, pos+0)
    rectleft = getshort(dat, pos+2)
    rectbot = getshort(dat, pos+4)
    rectright = getshort(dat, pos+6)
    return Rect(recttop, rectleft, rectbot, rectright)

def getsize(dat, pos):
    height = getshort(dat, pos+0)
    width = getshort(dat, pos+2)
    return Size(width, height)

def endnulls(script):
    # If the data has a null byte, delete it and anything that follows.
    pos = script.find(0)
    if pos >= 0:
        script = script[ : pos ]
    return script

def decode_script(script):
    """Turn the binary script data into a Python string.
    There may garbage at the end of the data block, after a null byte.
    We trim this off. Then we decode the classic Mac character set.
    """
    script = endnulls(script)
    if not len(script):
        return None
    script = script.decode('mac_roman')
    script = script.replace('\r', '\n')
    return script

def print_script(script, outfl, indent=0):
    """Print script text at the given indentation.
    """
    if not script:
        return
    tab = ' '*indent
    ls = script.rstrip().split('\n')
    for val in ls:
        outfl.write(tab)
        outfl.write(val)
        outfl.write('\n')

def parse(filename):
    """Parse a Hypercard stack file. Return a Stack object.
    """
    with open(filename, 'rb') as fl:
        dat = fl.read()
        
    stack = None
    pos = 0

    # Iterate through the stack's blocks.
    while pos < len(dat):
        bsize = getint(dat, pos+0)
        btype = dat[ pos+4 : pos+8 ].decode()
        bid = getsignint(dat, pos+8)
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
        elif btype == 'BKGD':
            bkgd = parse_background(block, bid)
            stack.backgrounds.append(bkgd)
        else:
            pass
        pos += bsize

    stack.finalize()
    return stack

# Parsers for the important block types.

def parse_stak(block, bid):
    format = getint(block, 0x10)
    numbackgrounds = getint(block, 0x24)
    numcards = getint(block, 0x2C)
    passwdhash = getint(block, 0x44)
    userlevel = getshort(block, 0x48)
    createversion = getversion(block, 0x60)
    modversion = getversion(block, 0x6C)
    cardrect = getrectangle(block, 0x78)
    pixsize = getsize(block, 0x1B8)
    script = block[ 0x600 : ]
    script = decode_script(script)
    stack = Stack(format, numbackgrounds, numcards, createversion, modversion, cardrect, pixsize, script)
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
    pos = parse_partstuff(card, block, 0x36)
    return card
        
def parse_background(block, bid):
    numcards = getint(block, 0x18)
    numparts = getshort(block, 0x24)
    numpartconts = getshort(block, 0x2C)
    bkgd = Background(bid, numparts, numpartconts)
    pos = parse_partstuff(bkgd, block, 0x32)
    return bkgd

def parse_partstuff(card, block, pos):
    # Parse the data which is included in both Cards and Backgrounds.
    for ix in range(card.numparts):
        partsize = getshort(block, pos+0)
        partid = getshort(block, pos+2)
        partname, npos = getstring(block, pos+30)
        rect = getrectangle(block, pos+6)
        part = CardPart(partid, partname, rect)
        if npos < pos+partsize:
            assert(block[npos] == 0)
            script = block[ npos+1 : pos+partsize ]
            script = decode_script(script)
            part.script = script

        card.parts.append(part)
        pos += partsize

    for ix in range(card.numpartconts):
        partid = getsignshort(block, pos+0)
        pcsize = getshort(block, pos+2)
        if block[pos+4] == 0:
            partstr = block[ pos+5 : pos+4+pcsize ]
        else:
            numruns = getshort(block, pos+4) & 0x7FFF
            partstr = block[ pos+6+2*numruns : pos+4+pcsize ]
        partstr = partstr.decode('mac_roman')
        partstr = partstr.replace('\r', '\n')
        card.partcontents.append( (partid, partstr) )
        pos += (4+pcsize)

        if pos & 1:
            # Undocumented alignment byte?
            pos += 1
        
    cardname, pos = getstring(block, pos)
    card.name = cardname
    script = block[ pos : ]
    script = decode_script(script)
    card.script = script

    return pos

if not args:
    print('usage: stakread.py [ -o OUTFILE ] hypercard.stak')
    sys.exit()
    
for filename in args:
    stack = parse(filename)
    if opts.outfile:
        if opts.outfile == '-':
            stack.dump(sys.stdout)
        else:
            with open(opts.outfile, 'w') as outfl:
                stack.dump(outfl)

    
    
