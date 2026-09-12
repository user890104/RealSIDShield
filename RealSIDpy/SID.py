import struct

from dataclasses import dataclass, field, fields

HEADER_V1 = struct.Struct(
    ">4s"    # magicID
    "H"      # version
    "H"      # dataOffset
    "H"      # loadAddress
    "H"      # initAddress
    "H"      # playAddress
    "H"      # songs
    "H"      # startSong
    "I"      # speed
    "32s"    # name
    "32s"    # author
    "32s"    # released
)

HEADER_V2 = struct.Struct(
    ">H"     # flags
    "B"      # startPage
    "B"      # pageLength
    "B"      # secondSIDAddress
    "B"      # thirdSIDAddress
)

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
        v1_fields = [
            f for f in fields(cls)
            if f.metadata.get('version', 1) == 1
        ]

        values = HEADER_V1.unpack(data[:HEADER_V1.size])

        cls_dict = dict(zip(
            (f.name for f in v1_fields),
            values,
        ))

        cls_dict['magicID'] = cls_dict['magicID'].decode('ascii')

        for key in ('name', 'author', 'released'):
            cls_dict[key] = cls_dict[key].rstrip(b'\0').decode('latin-1')

        if cls_dict['version'] >= 2:
            v2_fields = [
                f for f in fields(cls)
                if f.metadata.get('version', 1) == 2
            ]

            values = HEADER_V2.unpack(
                data[HEADER_V1.size:HEADER_V1.size + HEADER_V2.size]
            )

            cls_dict.update(dict(zip(
                (f.name for f in v2_fields),
                values,
            )))

        instance = cls(**cls_dict)
        instance.validate()

        return instance

    def validate(self):
        if self.magicID not in ('PSID', 'RSID'):
            raise ValueError(f'Unsupported file type: {self.magicID}')

        if self.version == 1 and self.dataOffset != 0x0076 or self.version in (2, 3, 4) and self.dataOffset != 0x007C:
            raise ValueError(f'Wrong dataOffset for version {sid.version}: {sid.dataOffset:04X}')

        if self.magicID == 'RSID' and (self.initAddress >= 0xA000 and self.initAddress < 0xC000 or self.initAddress >= 0xD000 or self.initAddress < 0x07E8):
            raise ValueError(f'Wrong initAddress for RSID: {self.initAddress:04X}')

        if self.songs < 1 or self.songs > 256:
            raise ValueError(f'Invalid number of songs: {self.songs}')

@dataclass
class Sid:
    header: SidHeader
    data: bytes

    @classmethod
    def from_bytes(cls, data: bytes):
        header = SidHeader.from_bytes(data)
        sid_data = data[header.dataOffset:]

        return cls(
            header=header,
            data=sid_data,
        )

    @classmethod
    def from_path(cls, path):
        with open(path, 'rb') as file:
            return cls.from_bytes(file.read())
