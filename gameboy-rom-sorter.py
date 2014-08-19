import os
import zipfile
import py7zlib
import struct
import bs4


# Some technical data

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


# Utilities

def extension_ok(file_name):
  return any(file_name.endswith(ext) for ext in ['.gb', '.gbc', '.zip', '.7z'])

def read_gb(file):
  file_data = file.read()
  file_data = struct.unpack('%dB' % (len(file_data)), file_data)
  #file.close() TODO close when necessary
  return file_data

def read_zip(path):
  files_data = []
  file_name = os.path.basename(path)
  zip = zipfile.ZipFile(path, 'r')
  for name in zip.namelist():
    file = zip.open(name)
    files_data += [read_gb(file)]
    zip.close()
  return files_data

def read_7z(path):
  files_data = []
  file_name = os.path.basename(path)
  sz = py7zlib.Archive7z(open(path, 'rb'))
  for name in sz.getnames():
    file = sz.getmember(next(m for m in sz.getnames()))
    files_data += [read_gb(file)]
  return files_data

def read_files(path):
  print('Reading file ' + path)
  files_data = []
  ext = os.path.splitext(path)[1]
  if ext == '.gb' or ext == '.gbc':
    files_data += [read_gb(open(path, 'rb'))]
  elif ext == '.zip':
    files_data += read_zip(path)
  elif ext == '.7z':
    files_data += read_7z(path)
  return files_data
  
# http://problemkaputt.de/pandocs.htm#thecartridgeheader
def get_rom_info(file_data):

  rom_data = {}
  
  rom_data['title'] = ''.join(map(lambda x: chr(x), file_data[0x134:0x144]))

  rom_data['SGB'] = 'Y' if file_data[0x146] == 0x03 else 'N'

  try:
    rom_data['type'] = mbcs[file_data[0x147]]
  except (IndexError, KeyError):
    rom_data['type'] = 'Unknown (' + format(file_data[0x147], '02x') + ')'

  try:
    rom_data['ROM'] = rom_sizes[file_data[0x148]]
  except (IndexError, KeyError):
    rom_data['ROM'] = 'Unknown (' + format(file_data[0x148], '02x') + ')'

  try:
    rom_data['RAM'] = ram_sizes[file_data[0x149]]
  except (IndexError, KeyError):
    rom_data['RAM'] = 'Unknown (' + format(file_data[0x149], '02x') + ')'

  return rom_data

# TODO clean up
def split_path(path):
  folders=[]
  while 1:
    path,folder=os.path.split(path)
    if folder!="":
      folders.append(folder)
    else:
      if path!="":
        folders.append(path)
      break
  folders.reverse()
  return folders


# Read ROMs

roms_data = []

for root, dirs, files in os.walk('roms'):
  for file in filter(extension_ok, files):

    # Read file(s)
    files_data = read_files(os.path.join(root, file))

    for file_data in files_data:

      # Extract ROM info
      rom_data = get_rom_info(file_data)

      # Add file name and category
      rom_data['file'] = os.path.splitext(file)[0]
      path_bits = split_path(os.path.join(root,file))
      rom_data['category'] = path_bits[1] if len(path_bits) > 2 else ''
      
      roms_data.append(rom_data)

    # Sort alphabetically
    roms_data.sort(key=lambda x: x['file'])


# Output to HTML

template = open('index_template.html', 'r')
soup = bs4.BeautifulSoup(template.read())
template.close()

table = soup.find('table')

def add_cell(row, content):
  cell = soup.new_tag('td')
  cell.append(unicode(content, errors='ignore')) # TODO fix this
  row.append(cell)

for rom_data in roms_data:

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

print('Done! Extracted data from ' + str(len(roms_data)) + ' ROMs')