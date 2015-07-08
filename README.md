This Python 2.7 script reads a bunch of Game Boy and Game Boy color ROMs in the `roms/` directory and outputs their specs to a filterable HTML file or a JSON dump. You can see an example listing most existing ROMs here: [HTML](http://merwanachibet.net/gameboy-roms.html)/[JSON](http://merwanachibet.net/gameboy-roms.json).

This can be useful for emulator developers who want to check which ROM to use in order to test a given feature (e.g. a specific memory bank controller, battery-backed RAM or Super GameBoy capabilities).

The script opens `.gb` and `.gbc` files. It is possible to categorize the ROMs in the output by putting them in separate sub-directories. For example:

    roms/
        games/
            Mustached Hero II.gb
            Mega Racing Deluxe.gbc
            some_archive.zip [containing "Super Plop Plop.gb"]
        demos/
            cooldemo.zip [containing "s0 l33t.gbc" and "s0 l33t II.gbc"]
        test_roms/
            cpu_test.gb
            sound_test.gb

Usage: `python generate-rom-list.py --help`
