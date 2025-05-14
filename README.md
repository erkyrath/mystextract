# Myst (1993) HyperCard Scripts

This repository contains the HyperTalk script code used in the 1993 Mac release of _Myst_, extracted from the game's HyperCard stacks.

The bulk of the game is, of course, media assets -- images, sounds, and video clips. Those are not included here. Nor does this contain a complete disassembly of the HyperCard stacks. I was only interested in the HyperTalk scripts, so I yoinked those out.

## What you'll find

The [scripts](./scripts/) directory contains the script dumps, one for each HyperCard stack in the original game.

- `_Myst.script`: The launcher. This is a self-executing stack which launches the game. (Note that the original filename was ` Myst`, with an initial space.)
- `Myst.script`: The scripts covering the main island.
- `Channelwood_Age.script`, `Mechanical_Age.script`, `Selenitic_Age.script`, `Stoneship_Age.script`: The scripts covering the four main puzzle Ages.
- `Dunny_Age.script`: The script covering the end-game Age. (The spelling was changed to "D'ni" in _Riven_ and later games, but in 1993 it was "Dunny".)
- `ALLRes.script`: Scripts having to do with saving and loading game state. The `ALLRes` file also contained sound resources, image resources, and HyperCard extensions; these resources are not included here.
- `CHRes1.script`, etc: Resource stacks (sounds and images). These contain no script data. Again, the resources are not included here.
- `Template.script`: Presumably a template used in development.

Note that in the original [Mac disk image][iso], the `_Myst` stack was at the root level. The five Age stacks were in a folder `Myst Files` which was meant to be copied to the player's hard drive. `ALLRes` and the rest of the stacks were in a folder `Myst Graphics` which remained on the CD-ROM. I have flattened this hierarchy for your browsing convenience.

Each `.script` file contains the script dump from one stack. The stack's global script is shown first. Then the stack's cards are listed. Each card has its own script, followed by the card's "parts" (buttons), each of which may have its own button-level script.

## What I did

I began with the [ISO disk image][iso] of _Myst_. Again, this is the 1993 Mac release. (The Windows port, and the later _Myst: Masterpiece Edition_, are not based on HyperCard.) 

[iso]: https://archive.org/details/Myst_The_Surrealistic_Adventure_That_Will_Become_Your_World_Broderbund_Cyan_1993

The disk image uses the classic Mac [HFS][] file system, which is not supported on modern machines. I used the [hfsutils][] package to extract the files.

[HFS]: https://en.wikipedia.org/wiki/Hierarchical_File_System_(Apple)
[hfsutils]: https://www.mars.org/home/rob/proj/hfs/

See [filelist](./filelist) for a file listing of the disk image. The file ` Myst` (the filename starts with a space) is the self-executing HyperCard stack which launches the game. The other files with type `MYag/MYST` are auxiliary stacks.

If you run the original HyperCard in a Mac-Classic emulator, it's quite possible to open and edit these stacks. They are password-protected, but not encrypted. There's a contemporary tool called [Deprotect][] which will let you remove the password.

(In 2024, Jeff Barbi was able to extract the original password: `oblio`. See [this video][barbivid] for that story.)

[Deprotect]: https://www.macintoshrepository.org/935-deprotect-a-hypercard-stack-
[barbivid]: https://www.youtube.com/watch?v=lacwEuMaQvQ

Anyhow, that's not what I did. I just wrote a Python script to parse the stack files and dump out the script code. The HyperCard stack format is documented [here][hcform1] and [here][hcform2].

[hcform1]: https://hypercard.org/hypercard_file_format_pierre/
[hcform2]: https://github.com/PierreLorenzi/HyperCardPreview/blob/master/StackFormat.md

## Other tools

Uli Kusterer's [stackimport][] tool is a much more complete Hypercard stack parser. It can extract images and (on the Mac filesystem) sounds as well. (C++, writes out XML data and PBM image files.)

(If I'd known about stackimport, I wouldn't have written my Python script! But I somehow missed it, even though I looked at Uli's Github page. Whoops. Well, I had fun.)

Pierre Lorenzi's [HyperCardPreview][] is a Mac GUI tool for browsing Hypercard stacks. However, I had trouble running it on current MacOS. It launches, but the Open File dialog won't recognize Hypercard files. (I think it's looking for classic Mac file type info, which hfsutils doesn't give you.)

[stackimport]: https://github.com/uliwitness/stackimport
[HyperCardPreview]: https://github.com/PierreLorenzi/HyperCardPreview/

Guillaume Lethuillier's [DeMystify][] uses stackimport to extract the node connection data from Myst and display it as a graph.

[DeMystify]: https://github.com/glthr/DeMystify
