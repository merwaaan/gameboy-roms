# -*- coding: utf-8 -*-
import argparse, bs4, itertools, json, os, py7zlib, struct, sys, threading, time, traceback, zipfile
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

rom_types = {
  0x00: '32 Kb',
  0x01: '64 Kb',
  0x02: '128 Kb',
  0x03: '256 Kb',
  0x04: '512 Kb',
  0x05: '1 Mb',
  0x06: '2 Mb',
  0x07: '4 Mb',
  0x52: '1.1 Mb',
  0x53: '1.2 Mb',
  0x54: '1.6 Mb'
}

ram_types = [
  '',
  '2 Kb',
  '8 Kb',
  '32 Kb'
]

# Structure containing the data extracted from one Game Boy ROM
Rom = namedtuple('Rom', ['filename', 'category', 'title', 'cart', 'ROM', 'RAM', 'SGB'])

# Parse the bytes from a ROM and return its specs
def parse_rom(data, filename, category):

  if args.verbose:
    print('Parsing "{}"...'.format(filename))

  # Extract the embedded title and remove NULL characters
  title = ''.join(map(lambda x: chr(x) if x < 128 else ' ', data[0x134:0x144]))
  title = filter(lambda x: ord(x) != 0, title)

  # Function for extracting the other fields
  def fetch(data, address, func):
    try:
      return func(data[address])
    except (IndexError, KeyError):
      return None

  sgb = fetch(data, 0x146, lambda x: x == 0x03)
  cart_type = fetch(data, 0x147, lambda x: cart_types[x])
  rom_type = fetch(data, 0x148, lambda x: rom_types[x])
  ram_type = fetch(data, 0x149, lambda x: ram_types[x])

  rom = Rom(filename, category, title, cart_type, rom_type, ram_type, sgb)

  if args.verbose:
    print('\t→ {}'.format(rom))

  return rom

# Read a ROM file and return its content
def read_rom(path):
  try:
    with open(path, 'rb') as file:
      data = file.read()
      bytes = struct.unpack('%dB' % len(data), data)
      return bytes
  except Exception as e:
    print('Error while reading ROM "{}": {}'.format(path, e))
    traceback.print_exc()

# Read and parse all the ROMs under the directory
def read_all(directory):

  for root, dirs, files in os.walk(directory):
    for file in files:

      name, extension = os.path.splitext(file)
      path = os.path.join(root, file)

      if extension in ['.gb', '.gbc']:
        rom = read_rom(path)

        # Get the original file name
        filename = os.path.basename(path)

        # The current directory is the category
        segments = path.split(os.sep)
        category = segments[1] if len(segments) > 2 else ''

        yield parse_rom(rom, filename, category)

# Output the extracted data to HTML
def html_output(roms, output_name):

  with open('template.html', 'r') as template:
    soup = bs4.BeautifulSoup(template.read())

  table = soup.find('table')

  # Add a cell to the table and fill it
  def add_cell(row, content):
    text = content if content is not None else '?' #content.decode('unicode-escape') if content is not None else '?'
    cell = soup.new_tag('td')
    cell.append(text)
    cell['title'] = text
    row.append(cell)

  # Align content with non-breaking spaces
  def align(content, type):
    return '&nbsp;' * ((6 if type == 'ROM' else 5) - len(content)) + content

  for rom in roms:

    row = soup.new_tag('tr')
    for field in ['filename', 'title', 'cart', 'ROM', 'RAM', 'SGB', 'category']:

      value = getattr(rom, field)

      # Special treatment for the SGB flag: use a check mark when outputting to HTML
      if field == 'SGB':
        value = u'✓' if value else u'✗'
      # Special treatment for ROM and RAM: align on the unit
      elif field in ['ROM', 'RAM'] and value is not None and len(value) > 0:
        value = align(value, field)

      add_cell(row, value)

    table.append(row)

  name = output_name if output_name.endswith('.html') else output_name + '.html'
  with open(name, 'w') as output:
   output.write(soup.encode_contents(formatter=None))

# Output the extracted data to JSON
def json_output(roms, output_name):

  name = output_name if output_name.endswith('.json') else output_name + '.json'
  with open(name, 'w') as output:
    json.dump([rom._asdict() for rom in roms], output, indent=2)

# Main

parser = argparse.ArgumentParser(description='Extract data from Game Boy Roms and output it to HTML.')
parser.add_argument('-v', '--verbose', help='print details during the process', action='store_true')
parser.add_argument('-d', '--dir', help='name of the root directory containing the ROMs', default='roms')
parser.add_argument('-o', '--output', help='name of the output file' , default='gameboy-roms')
parser.add_argument('-t', '--type', help='type of the formatted output', choices=['html', 'json', 'both'], default='html')
args = parser.parse_args()

print('Parsing data from the "{}" directory...'.format(args.dir))

roms = list(read_all(args.dir))

if len(roms) == 0:
  print('No ROMs found')
else:
  roms.sort(key=lambda rom: rom.filename.lower())
  if args.type in ['html', 'both']:
    html_output(roms, args.output)
  if args.type in ['json', 'both']:
    json_output(roms, args.output)
  print('Finished! Data about {} ROMs has been output to "{}".'.format(len(roms), args.output))
