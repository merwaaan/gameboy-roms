# -*- coding: utf-8 -*-
import argparse, bs4, itertools, os, py7zlib, struct, sys, threading, time, traceback, zipfile
from collections import namedtuple

# http://problemkaputt.de/pandocs.htm#thecartridgeheader
cart_types = {
  0x00: 'ROM ONLY',
  0x01: 'MBC1',
  0x02: 'MBC1+RAM',
  0x03: 'MBC1+RAM+BATTERY',
  0x05: 'MBC2',
  0x06: 'MBC2+BATTERY',
  0x08: 'ROM+RAM',
  0x09: 'ROM+RAM+BATTERY',
  0x0B: 'MMM01',
  0x0C: 'MMM01+RAM',
  0x0D: 'MMM01+RAM+BATTERY',
  0x0F: 'MBC3+TIMER+BATTERY',
  0x10: 'MBC3+TIMER+RAM+BATTERY',
  0x11: 'MBC3',
  0x12: 'MBC3+RAM',
  0x13: 'MBC3+RAM+BATTERY',
  0x15: 'MBC4',
  0x16: 'MBC4+RAM',
  0x17: 'MBC4+RAM+BATTERY',
  0x19: 'MBC5',
  0x1A: 'MBC5+RAM',
  0x1B: 'MBC5+RAM+BATTERY',
  0x1C: 'MBC5+RUMBLE',
  0x1D: 'MBC5+RUMBLE+RAM',
  0x1E: 'MBC5+RUMBLE+RAM+BATTERY',
  0xFC: 'POCKET CAMERA',
  0xFD: 'BANDAI TAMA5',
  0xFE: 'HuC3',
  0xFF: 'HuC1+RAM+BATTERY'
}

rom_sizes = {
  0x00: '&nbsp;32 Kb',
  0x01: '&nbsp;64 Kb (4 banks)',
  0x02: '128 Kb (8 banks)',
  0x03: '256 Kb (16 banks)',
  0x04: '512 Kb (32 banks)',
  0x05: '&nbsp;&nbsp;1 Mb (64 banks)',
  0x06: '&nbsp;&nbsp;2 Mb (128 banks)',
  0x07: '&nbsp;&nbsp;4 Mb (256 banks)',
  0x52: '1.1 Mb (72 banks)',
  0x53: '1.2 Mb (80 banks)',
  0x54: '1.6 Mb Kb (96 banks)'
}

ram_sizes = [
  '',
  '&nbsp;2 Kb',
  '&nbsp;8 Kb',
  '32 Kb'
]

# Structure containing the data extracted from Game Boy ROMs
Rom = namedtuple('Rom', ['filename', 'category', 'title', 'SGB', 'cart', 'ROM', 'RAM'])

# Parse the bytes from a ROM and return its specs
def parse_rom(rom, filename, category):

  if args.verbose:
    print('Parsing "{}"...'.format(filename))

  title = ''.join(map(lambda x: chr(x), rom[0x134:0x144]))
  SGB = 'Y' if rom[0x146] == 0x03 else 'N'
  cart = cart_types[rom[0x147]]
  ROM = rom_sizes[rom[0x148]]
  RAM = ram_sizes[rom[0x149]]

  rom = Rom(filename, category, title, SGB, cart, ROM, RAM)

  if args.verbose:
    print('\t↳ {}'.format(rom))

  return rom

# File reading utilities

def bytes(data):
  return struct.unpack('%dB' % len(data), data)

def read_gb(path):
  try:
    with open(path, 'rb') as file:
      yield (bytes(file.read()), os.path.basename(path))
  except Exception as e:
    print('Error while reading ROM "{}": {}'.format(path, e))
    traceback.print_exc()

def read_zip(path):
  try:
    with zipfile.ZipFile(path, 'r') as zip:
      names = [name for name in zip.namelist() if name.endswith('.gb') or name.endswith('.gbc')]
      for name in names:
        yield (bytes(zip.read(name)), name)
  except Exception as e:
    print('Error while reading ZIP archive "{}": {}'.format(path, e))
    traceback.print_exc()

def read_7z(path):
  try:
    with open(path, 'rb') as file:
      zip = py7zlib.Archive7z(file)
      names = [name for name in zip.getnames() if name.endswith('.gb') or name.endswith('.gbc')]
      for name in names:
        yield (bytes(zip.getmember(name).read()), name)
  except Exception as e:
    print('Error while reading 7Z archive "{}": {}'.format(path, e))
    traceback.print_exc()

handlers = {
  #'.zip': read_zip,
  #'.7z': read_7z,
  '.gb': read_gb,
  '.gbc': read_gb
}

# Read and parse all the ROMs under the directory
def read_all(directory):

  for root, dirs, files in os.walk(directory):
    for file in files:

      name, extension = os.path.splitext(file)
      path = os.path.join(root, file)
      segments = path.split(os.sep)
      category = segments[1] if len(segments) > 2 else ''

      try:

        # Get the file content and parse it
        # (may be several ROMs if the file is an archive)
        handler = handlers[extension.lower()]
        for rom, filename in handler(path):
          yield parse_rom(rom, filename, category)

      except KeyError as e:
        if args.verbose:
          print('Ignoring "{}" (unsupported extension).'.format(file))

# Output the extracted specs to HTML
def html_output(roms, output_name):

  with open('template.html', 'r') as template:
    soup = bs4.BeautifulSoup(template.read())

  table = soup.find('table')

  def add_cell(row, content):
    cell = soup.new_tag('td')
    text = unicode(content, errors='ignore')
    cell.append(text)
    cell['title'] = text
    row.append(cell)

  for rom in roms:
    row = soup.new_tag('tr')
    for field in ['filename', 'title', 'cart', 'ROM', 'RAM', 'SGB', 'category']:
      add_cell(row, getattr(rom, field))
    table.append(row)

  with open(output_name, 'w') as output:
   output.write(soup.encode_contents(formatter=None))


# Main

parser = argparse.ArgumentParser(description='Extract data from Game Boy Roms and output it to HTML.')
parser.add_argument('-v', '--verbose', help='print more details', action='store_true')
parser.add_argument('-d', '--dir', help='name of the root directory containing the ROMs', default='roms')
parser.add_argument('-o', '--output', help='name of the output HTML file', default='index.html')
args = parser.parse_args()

print('Parsing data from the "{}" directory...'.format(args.dir))
roms = list(read_all(args.dir))
roms.sort(key=lambda rom: rom.filename.lower())
html_output(roms, args.output)
print('Finished! The parsed data has been output to "{}".'.format(args.output))
