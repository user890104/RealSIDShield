"""
SID.py
"""

from struct import Struct
from dataclasses import dataclass, field, fields
from os import PathLike

HEADER_V1 = Struct(
    '>4s'    # magicID
    'H'      # version
    'H'      # dataOffset
    'H'      # loadAddress
    'H'      # initAddress
    'H'      # playAddress
    'H'      # songs
    'H'      # startSong
    'I'      # speed
    '32s'    # name
    '32s'    # author
    '32s'    # released
)

HEADER_V2 = Struct(
    '>H'     # flags
    'B'      # startPage
    'B'      # pageLength
    'B'      # secondSIDAddress
    'B'      # thirdSIDAddress
)

PROGRAM_DATA_ADDRESS = Struct('<H')


def validate_sid_address(value, field_name):
    if value == 0:
        return

    if value < 0x42 or value > 0xFE or value & 1:
        raise ValueError(f'Invalid {field_name}: {value:02X}')


@dataclass
class SidHeader:
    magicID: str
    version: int
    dataOffset: int
    loadAddress: int
    initAddress: int
    playAddress: int
    songs: int
    startSong: int
    speed: int
    name: str
    author: str
    released: str
    flags: int = field(default=None, metadata={'version': 2})
    startPage: int = field(default=None, metadata={'version': 2})
    pageLength: int = field(default=None, metadata={'version': 2})
    secondSIDAddress: int = field(default=None, metadata={'version': 2})
    thirdSIDAddress: int = field(default=None, metadata={'version': 2})

    @classmethod
    def from_bytes(cls, data: bytes) -> 'SidHeader':
        if len(data) < HEADER_V1.size:
            raise ValueError(f'SID file is too short: {len(data)} bytes (minimum {HEADER_V1.size})')

        v1_fields = [
            f for f in fields(cls)
            if f.metadata.get('version', 1) == 1
        ]

        values = dict(zip(
            (f.name for f in v1_fields),
            HEADER_V1.unpack(data[:HEADER_V1.size]),
        ))

        version = values['version']
        if version not in (1, 2, 3, 4):
            raise ValueError(f'Unsupported SID version: {version}')

        values['magicID'] = values['magicID'].decode('ascii')

        for key in ('name', 'author', 'released'):
            values[key] = values[key].rstrip(b'\0').decode('latin-1')

        if version >= 2:
            if len(data) < HEADER_V1.size + HEADER_V2.size:
                raise ValueError(f'SID file is too short for version {version} header')

            v2_fields = [
                f for f in fields(cls)
                if 1 < f.metadata.get('version', 1) <= version
            ]

            values.update(dict(zip(
                (f.name for f in v2_fields),
                HEADER_V2.unpack(
                    data[HEADER_V1.size:HEADER_V1.size + HEADER_V2.size]
                ),
            )))

        instance = cls(**values)
        instance.validate()

        return instance

    def validate(self) -> None:
        if self.magicID not in ('PSID', 'RSID'):
            raise ValueError(f'Unsupported file type: {self.magicID}')

        if self.magicID == 'RSID':
            self.validate_rsid()

        expected_offset = 0x76 if self.version == 1 else 0x7C

        if self.dataOffset != expected_offset:
            raise ValueError(f'Wrong dataOffset for version {self.version}: {self.dataOffset:04X}')

        if not 1 <= self.songs <= 256:
            raise ValueError(f'Invalid number of songs: {self.songs}')

        if not 1 <= self.startSong <= self.songs:
            raise ValueError(f'Invalid startSong: {self.startSong} (songs={self.songs})')

        if self.version >= 2:
            if self.startPage in (0, 0xFF):
                if self.pageLength != 0:
                    raise ValueError(f'Invalid pageLength {self.pageLength:02X} for startPage {self.startPage:02X}')

        if self.version == 2 and self.secondSIDAddress != 0:
            raise ValueError('v2 secondSIDAddress must be 00')

        if self.version <= 3 and self.thirdSIDAddress != 0:
            raise ValueError(f'v{self.version} thirdSIDAddress must be 00')

        validate_sid_address(self.secondSIDAddress, 'secondSIDAddress')
        validate_sid_address(self.thirdSIDAddress, 'thirdSIDAddress')

        if (
            self.secondSIDAddress
            and self.thirdSIDAddress
            and self.secondSIDAddress == self.thirdSIDAddress
        ):
            raise ValueError('Second and third SID addresses must differ')

        if self.flags & 0xFC00:
            raise ValueError(f'Reserved flags are set: {self.flags:04X}')

    def validate_rsid(self):
        if self.version not in (2, 3, 4):
            raise ValueError(f'RSID requires version 2, 3, or 4: {self.version}')

        if self.loadAddress != 0:
            raise ValueError(f'RSID loadAddress must be 0000: {self.loadAddress:04X}')

        if self.playAddress != 0:
            raise ValueError(f'RSID playAddress must be 0000: {self.playAddress:04X}')

        if self.speed != 0:
            raise ValueError(f'RSID speed must be 00000000: {self.speed:08X}')

        if self.initAddress < 0x07E8:
            raise ValueError(f'RSID initAddress below $07E8: {self.initAddress:04X}')

        if 0xA000 <= self.initAddress < 0xC000:
            raise ValueError(f'RSID initAddress in ROM area: {self.initAddress:04X}')

        if self.initAddress >= 0xD000:
            raise ValueError(f'RSID initAddress in ROM/I/O area: {self.initAddress:04X}')

    def speed_for_song(self, song: int) -> int:
        if self.version <= 2 or (self.flags & 0x02):
            bit = (song - 1) % 32
        else:
            bit = min(song - 1, 31)

        return (self.speed >> bit) & 1


@dataclass
class Sid:
    header: SidHeader
    data: bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Sid':
        header = SidHeader.from_bytes(data[:HEADER_V1.size + HEADER_V2.size])

        if len(data) < header.dataOffset:
            raise ValueError(f'SID dataOffset {header.dataOffset:04X} exceeds file size {len(data):04X}')

        sid_data = data[header.dataOffset:]

        return cls(
            header=header,
            data=sid_data,
        )

    @classmethod
    def from_path(cls, path: str | PathLike[str]) -> 'Sid':
        with open(path, 'rb') as file:
            return cls.from_bytes(file.read())
