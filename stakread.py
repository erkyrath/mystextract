#!/usr/bin/env python3

import sys
import struct

if len(sys.argv) <= 1:
    print('usage: stakread.py hypercard.stak')
    sys.exit()

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
    val = dat[ pos : ix ]
    return val, ix+1

def endnulls(script):
    while len(script) and script[0] == 0:
        script = script[ 1 : ]
    while len(script) and script[-1] == 0:
        script = script[ : -1 ]
    return script

def parse(filename):
    with open(filename, 'rb') as fl:
        dat = fl.read()
    pos = 0
    while pos < len(dat):
        bsize = getint(dat, pos+0)
        btype = dat[ pos+4 : pos+8 ].decode()
        bid = getsint(dat, pos+8)
        #print(bsize, btype, bid)
        block = dat[ pos : pos+bsize ]
        if btype == 'STAK':
            parse_stak(block, bid)
        elif btype == 'LIST':
            parse_list(block, bid)
        elif btype == 'CARD':
            parse_card(block, bid)
            #break ###
        else:
            print('%s %d:' % (btype, bid,))
        pos += bsize

def parse_stak(block, bid):
    print('STAK %d:' % (bid,))
    format = getint(block, 16)
    print('  Format:', format)
    script = block[ 0x600 : ]
    script = script.decode('mac_roman')
    ###print('     %r' % (script,))

def parse_list(block, bid):
    print('LIST %d:' % (bid,))
    numpages = getint(block, 0x10)
    print('  NumPages:', numpages)
    pagesize = getint(block, 0x14)
    print('  PageSize:', pagesize)
    numcards = getint(block, 0x18)
    print('  NumCards:', numcards)
    cardrefsize = getshort(block, 0x1C)
    print('  CardRefSize:', cardrefsize)
    for ix in range(numpages):
        pos = 0x30 + 6*ix
        pbid = getint(block, pos)
        pcards = getshort(block, pos+4)
        print('  ...page %d: block ID %d, %d cards' % (ix, pbid, pcards,))

def parse_card(block, bid):
    print('CARD %d:' % (bid,))
    pbid = getint(block, 0x20)
    print('  PageBlockID:', pbid)
    background = getint(block, 0x24)
    print('  Background:', background)
    numparts = getshort(block, 0x28)
    print('  NumParts:', numparts)
    numpartconts = getshort(block, 0x30)
    print('  NumPartConts:', numpartconts)

    pos = 0x36
    for ix in range(numparts):
        partsize = getshort(block, pos+0)
        partid = getshort(block, pos+2)
        partname, npos = getstring(block, pos+30)
        recttop = getshort(block, pos+6)
        rectleft = getshort(block, pos+8)
        rectbot = getshort(block, pos+10)
        rectright = getshort(block, pos+12)
        print('  ...part %d: ID %d %r' % (ix, partid, partname))
        print('     rect: t=%d l=%d b=%d r=%d' % (recttop, rectleft, rectbot, rectright,))
        if npos < pos+partsize:
            assert(block[npos] == 0)
            script = block[ npos+1 : pos+partsize ]
            script = endnulls(script)
            script = script.decode('mac_roman').replace('\r', '\n')
            if script:
                print('     %r' % (script,))
        pos += partsize

    for ix in range(numpartconts):
        partid = getshort(block, pos+0)
        pcsize = getshort(block, pos+2)
        if block[pos+4] == 0:
            partstr = block[ pos+5 : pos+4+pcsize ]
        else:
            numruns = getshort(block, pos+4) & 0x7FFF
            partstr = block[ pos+6+2*numruns : pos+4+pcsize ]
        partstr = partstr.decode()
        print('  ...partcont %d: part %d %r' % (ix, partid, partstr))
        pos += (4+pcsize)

    script = block[ pos : ]
    script = endnulls(script)
    script = script.decode('mac_roman').replace('\r', '\n')
    if script:
        print('  ...script: %r' % (script,))

        
for filename in sys.argv[ 1 : ]:
    parse(filename)
    
