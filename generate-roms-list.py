import os
import zipfile
import py7zlib
import struct
import bs4
import itertools


#
# Codes for embedded cartridge specs
# http://problemkaputt.de/pandocs.htm#thecartridgeheader
#

mbcs = {
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


#
# Utilities for handling archives
#

def extract_zip(path):

  extracted = []

  zip = zipfile.ZipFile(path);

  for name in [name for name in zip.namelist() if name.lower().endswith('.gb') or name.lower().endswith('.gbc')]:

    zip.extract(name, os.path.dirname(path))

    extracted.append(os.path.join(os.path.dirname(path), name))
    print('Extracted %s' % (name))

  zip.close()

  return extracted


def extract_7z(path):

  extracted = []

  with open(path, 'rb') as file:

    zip = py7zlib.Archive7z(file)

    for name in [name for name in zip.getnames() if name.endswith('.gb') or name.endswith('.gbc')]:

      rom_path = os.path.join(os.path.dirname(path), name)

      rom = open(rom_path, 'wb')
      rom.write(zip.getmember(name).read())
      rom.close()

      extracted.append(rom_path)
      print('Extracted %s' % (name))

  return extracted


def extract_all():

  for root, dirs, files in os.walk('roms'):
    for file in files:

      name, extension = os.path.splitext(file)

      if extension == '.zip':
        yield extract_zip(os.path.join(root, file))
      elif extension == '.7z':
        yield extract_7z(os.path.join(root, file))


def clean_up(to_delete):

  for path in to_delete:

    try:
      os.remove(path)
      print('Cleaned up %s' % (path))

    except OSError as e:
      print('Cannot delete %s, you may have to delete it manually' % (path))
      print(e)


#
# ROM reading & parsing
#

def read_rom(path):

  print('Reading %s' % (path))

  file_data = []

  with open(path, 'rb') as file:
    file_data = file.read()
    file_data = struct.unpack('%dB' % (len(file_data)), file_data)

  return file_data


def parse_rom(file_data):

  # http://problemkaputt.de/pandocs.htm#thecartridgeheader

  rom_data = {}

  rom_data['title'] = ''.join(map(lambda x: chr(x), file_data[0x134:0x144]))

  try:
    rom_data['SGB'] = 'Y' if file_data[0x146] == 0x03 else 'N'
  except (IndexError, KeyError):
    rom_data['SGB'] = '?'

  try:
    rom_data['type'] = mbcs[file_data[0x147]]
  except (IndexError, KeyError):
    rom_data['type'] = '?)'

  try:
    rom_data['ROM'] = rom_sizes[file_data[0x148]]
  except (IndexError, KeyError):
    rom_data['ROM'] = '?'

  try:
    rom_data['RAM'] = ram_sizes[file_data[0x149]]
  except (IndexError, KeyError):
    rom_data['RAM'] = '?'

  return rom_data


def read_roms():

  roms_data = []

  for root, dirs, files in os.walk('roms'):
    for file in files:

      name, extension = os.path.splitext(file)

      # Only consider GameBoy ROMs
      if (extension.lower() not in ['.gb', '.gbc']):
        continue;

      # Read the file
      file_data = read_rom(os.path.join(root, file))
      rom_data = parse_rom(file_data)

      # Add file name and category
      rom_data['file'] = name
      path_bits = os.path.join(root, file).split(os.sep)
      rom_data['category'] = path_bits[1] if len(path_bits) > 2 else ''

      roms_data.append(rom_data)

    # Sort alphabetically
    roms_data.sort(key=lambda x: x['file'])

  return roms_data


#
# Output to HTML
#

def html_output(data):

  template = open('index_template.html', 'r')
  soup = bs4.BeautifulSoup(template.read())
  template.close()

  table = soup.find('table')

  def add_cell(row, content):
    cell = soup.new_tag('td')
    cell.append(unicode(content, errors='ignore'))
    row.append(cell)

  for rom_data in data:

    row = soup.new_tag('tr')
    table.append(row)

    add_cell(row, rom_data['file'])
    add_cell(row, rom_data['title'])
    add_cell(row, rom_data['type'])
    add_cell(row, rom_data['ROM'])
    add_cell(row, rom_data['RAM'])
    add_cell(row, rom_data['SGB'])
    add_cell(row, rom_data['category'])

  output = open('index.html', 'w+')
  output.write(soup.encode_contents(formatter=None))
  output.close()


#
# Main
#

try:

  extracted = []
  for e in extract_all():
    extracted += e # Extract compressed ROMs

  data = read_roms() # Read and parse the ROMs
  html_output(data) # Populate the template

  print('Done! ' + str(len(data)) + ' ROMs were listed.')

except KeyboardInterrupt:

  pass

finally:

  clean_up(extracted) # Delete the uncompressed ROMs

