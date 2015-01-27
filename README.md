This Python script reads a bunch of GameBoy and GameBoy color ROMs in the `roms/` directory and outputs a HTML page with some technical data. You can see an example listing most existing ROMs on [this page](http://merwanachibet.net/gameboy-roms-list.html) (coming soon).

This can be useful for emulator developers who want to determine which ROM to use in order to test a given feature (e.g. a specific memory bank controller, battery-backed RAM or Super GameBoy capabilities).

The script opens `.gb` and `.gbc` files. It will also look inside of `.zip` and `.7z` archives (the contained ROMs will be temporarily decompressed and then deleted at the end of the script).

It is possible to categorize the ROMs in the HTML output by putting them in separate sub-directories of `roms/`. For example:

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

