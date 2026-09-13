from struct import Struct
from dataclasses import dataclass, field, fields

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
    def from_bytes(cls, data):
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

    def validate(self):
        if self.magicID not in ('PSID', 'RSID'):
            raise ValueError(f'Unsupported file type: {self.magicID}')

        if self.version == 1 and self.dataOffset != 0x0076 or self.version in (2, 3, 4) and self.dataOffset != 0x007C:
            raise ValueError(f'Wrong dataOffset for version {self.version}: {self.dataOffset:04X}')

        if self.magicID == 'RSID' and (self.initAddress >= 0xA000 and self.initAddress < 0xC000 or self.initAddress >= 0xD000 or self.initAddress < 0x07E8):
            raise ValueError(f'Wrong initAddress for RSID: {self.initAddress:04X}')

        if not 1 <= self.songs <= 256:
            raise ValueError(f'Invalid number of songs: {self.songs}')

        if not 1 <= self.startSong <= self.songs:
            raise ValueError(f'Invalid startSong: {self.startSong} (songs={self.songs})')

    def speed_for_song(self, song):
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
    def from_bytes(cls, data: bytes):
        header = SidHeader.from_bytes(data[:HEADER_V1.size + HEADER_V2.size])

        if len(data) < header.dataOffset:
            raise ValueError(f'SID dataOffset {header.dataOffset:04X} exceeds file size {len(data):04X}')

        sid_data = data[header.dataOffset:]

        return cls(
            header=header,
            data=sid_data,
        )

    @classmethod
    def from_path(cls, path):
        with open(path, 'rb') as file:
            return cls.from_bytes(file.read())
