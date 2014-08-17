#WIP!

This Python script reads a bunch of GameBoy and GameBoy color ROMs in the `roms/` directory and outputs a HTML page with some technical data.

This can be useful for emulator developers who want to determine which ROM to use in order to test a given feature. For example, a specific memory bank controller, battery-backed RAM or Super GameBoy capabilities.

The script opens `.gb` and `.gbc` files. It will also look inside of `.zip` archives given that the contained file shares the same name, as is often the case (for example `My Awesome Rom (U) [!].zip` contains `My Awesome Rom (U) [!].gb`).

It is additionally possible to categorize the ROMs in the HTML output, by putting them in separate sub-directories of `roms/`. For example:

    roms/
        games/
            rom1.gb
            rom2.gbc
            foo.zip [containing rom3.gb]
        demos/
            bar.zip [containing rom4.gbc, rom5.gb]
            rom6.gb
        test_roms/
            rom7.gbc


### TODO
- add Javascript to sort/filter rows on the output page
- read .7z files