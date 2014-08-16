import os
import struct
from bs4 import BeautifulSoup, Tag


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
  0x00: '32 Kb (no banking)',
  0x01: '64 Kb (4 banks)',
  0x02: '128 Kb (8 banks)',
  0x03: '256 Kb (16 banks)',
  0x04: '512 Kb (32 banks)',
  0x05: '1 Mb (64 banks)',
  0x06: '2 Mb (128 banks)',
  0x07: '4 Mb (256 banks)',
  0x52: '1.1 Mb (72 banks)',
  0x53: '1.2 Mb (80 banks)',
  0x54: '1.6 Mb Kb (96 banks)'
}

ram_sizes = [
  'None',
  '2 Kb',
  '8 Kb',
  '32 Kb (4 banks)'
]


# Read the ROMS

roms = [file for file in os.listdir('./roms') if file.endswith('.gb')]

roms_data = []

for rom in roms:

  file = open('./roms/' + rom, 'rb')
  file_data = file.read()
  file_data = struct.unpack('%dB' % (len(file_data)), file_data)
  file.close()

  # http://problemkaputt.de/pandocs.htm#thecartridgeheader

  rom_data = {}
  rom_data['file'] = os.path.splitext(rom)[0]
  rom_data['title'] = ''.join(map(lambda x: chr(x), file_data[0x134:0x144]))
  rom_data['SGB'] = file_data[0x146] == 0x03
  rom_data['type'] = file_data[0x147]
  rom_data['ROM'] = file_data[0x148]
  rom_data['RAM'] = file_data[0x149]

  roms_data.append(rom_data)

print(roms_data)


# Output to HTML

template = open('index_template.html', 'r')
soup = BeautifulSoup(template.read())
template.close()

table = soup.find('table')

def add_cell(row, content):
  cell = soup.new_tag('td')
  cell.append(content)
  row.append(cell)

for rom_data in roms_data:

  row = soup.new_tag('tr')
  table.append(row)

  add_cell(row, rom_data['file'])
  add_cell(row, rom_data['title'])
  add_cell(row, mbcs[rom_data['type']])
  add_cell(row, rom_sizes[rom_data['ROM']])
  add_cell(row, ram_sizes[rom_data['RAM']])
  add_cell(row, 'Y' if rom_data['SGB'] else 'N')

print(soup.prettify())

output = open('index.html', 'w+')
output.write(soup.prettify())
output.close()