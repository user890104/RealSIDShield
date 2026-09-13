#!/usr/bin/env python3

'''
RealSID.py
Version 1.0

Copyright (c) 2013, A.T.Brask (atbrask[at]gmail[dot]com)
All rights reserved,

Very rudimentary SID player for demonstrating the RealSIDShield Arduino shield.
Basically, it emulates a 6502 CPU with 64KB of memory. No VIC or CIA chips.
It works by running the play routine at ~50 Hz. After each run, it updates the
registers in real SID chip connected via the Arduino.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

from time import sleep
from argparse import ArgumentParser
from struct import unpack
from serial import Serial
from py65.devices import mpu6502
from SID import Sid, PROGRAM_DATA_ADDRESS

video_standard_text = ['Unknown', 'PAL', 'NTSC', 'PAL/NTSC']

def run_cpu(cpu, new_pc, new_a, new_x, new_y):
    cpu.pc = new_pc
    cpu.a = new_a
    cpu.x = new_x
    cpu.y = new_y
    cpu.sp = 0xFF
    running = True
    instruction_count = 0

    while running and instruction_count < 1_000_000:
        ## Test for return instructions RTI (0x40) and RTS (0x60)
        if cpu.ByteAt(cpu.pc) in (0x40, 0x60) and cpu.sp == 0xFF:
            running = False

        ## Test for BRK (0x00)
        if cpu.ByteAt(cpu.pc) == 0x00:
            running = False

        ## Step one instruction
        cpu.step()
        instruction_count += 1

        ## Test for jump into Kernal interrupt handler exit
        if (cpu.ByteAt(0x01) & 0x07) != 0x05 and cpu.pc in (0xea31, 0xea81):
            running = False

    return instruction_count

def play_sid(filename, song, play_seconds, port, baud_rate):
    ## Parse file
    sid = Sid.from_path(filename)
    header = sid.header

    print(f'SID type: {header.magicID} (version {header.version})')

    if header.magicID == 'RSID':
        print('Warning: RSID files may not play properly. YMMV.')

    print(f'Data offset: {header.dataOffset:04X}')
    print(f'Load address: {header.loadAddress:04X}')
    print(f'Init address: {header.initAddress:04X}')
    print(f'Play address: {header.playAddress:04X}')

    print(f'Found {header.songs} song(s) (default song is {header.startSong})')
    if song < 1 or song > header.songs:
        if song != -1:
            print(f'Invalid song specific ({song}), playing the start song instead ({header.startSong})')
        song = header.startSong

    print(f'Song {song} selected')

    #print('Speed: {0:08X}'.format(header.speed))
    song_speed = (header.speed >> (song - 1)) & 0x1

    if song_speed == 0:
        if header.version >= 2:
            video_standard = (header.flags >> 2) & 0x3
            print(f'Video standard: {video_standard_text[video_standard]}')

            if video_standard == 1:
                playback_frequency = 50 # PAL
            if video_standard == 2:
                playback_frequency = 60 # NTSC
            else:
                playback_frequency = 50 # Unknown or PAL/NTSC
        else:
            playback_frequency = 50 # Default for v1 is PAL

        print(f'Using {playback_frequency}Hz vertical blank interrupt.')
    else:
        print('Using the CIA 1 timer @ 60Hz.')
        playback_frequency = 60

    print(f'Title    : {header.name}')
    print(f'Author   : {header.author}')
    print(f'Released : {header.released}')

    data_offset = 0

    ## Check load address
    if header.loadAddress == 0:
        print('Warning: SID has load address 0, reading from C64 binary data')
        load_address = PROGRAM_DATA_ADDRESS.unpack(sid.data[:2])[0]
        data_offset = 2
        print(f'New load address is {load_address:04X}')
    else:
        load_address = header.loadAddress

    ## Check init address
    if header.initAddress == 0:
        print('Warning: SID has init address 0, cloning load address instead')
        init_address = load_address
        print(f'New init address is {init_address:04X}')
    else:
        init_address = header.initAddress

    ## Setup memory
    memory = [0] * 0x10000
    memory[0x01] = 0x37
    program = sid.data[data_offset:]

    if load_address + len(program) > 0x10000:
        raise ValueError(f'SID data does not fit in C64 memory: {load_address:04X} + {len(program):04X}')

    for idx, byte in enumerate(program):
        memory[load_address + idx] = byte

    ## Setup CPU
    cpu = mpu6502.MPU(memory)

    ## Init SID tune
    print(f'Initializing song {song}...')
    run_cpu(cpu, init_address, song - 1, 0, 0)

    ## Check play address
    if header.playAddress == 0:
        print('Warning: SID has play address 0, reading from interrupt vector')

        if (memory[0x01] & 0x07) == 0x05:
            play_address = PROGRAM_DATA_ADDRESS.unpack(memory[0xfffe:0x10000])[0]
        else:
            play_address = PROGRAM_DATA_ADDRESS.unpack(memory[0x314:0x316])[0]

        print(f'New play address is {play_address:04X}')
    else:
        play_address = header.playAddress

    ## Init RealSIDShield and wait for it to reset properly
    print(f'Using serial port {port} at {baud_rate} baud...')
    print('Initializing serial connection to the Arduino...')
    serial_port = Serial(port=port, baudrate=baud_rate, timeout=0.1)
    sleep(0.01)
    serial_port.reset_input_buffer()

    print('Connecting...', end='', flush=True)
    retries = 30
    while serial_port.read() != b'?' and retries > 0:
        retries -= 1
        print('.', end='', flush=True)

    print()

    if retries == 0:
        print('Connection timed out')
        serial_port.close()
        return

    ## Configure the speed
    config_cmd = [0] * 26
    config_cmd[0] = 1 # type=config
    config_cmd[1] = round(1000 / playback_frequency)
    serial_port.write(config_cmd)
    serial_port.flush()

    ## Play SID tune!
    if play_seconds == -1:
        print('Playing...')
    else:
        print(f'Playing for {play_seconds} seconds...')

    play_calls = 0
    retries = 10

    while (play_seconds == -1 or play_calls < play_seconds * playback_frequency) and retries > 0:
        try:
            request = serial_port.read()
        except KeyboardInterrupt:
            # config_cmd resets the SID, which stops the sound
            serial_port.write(config_cmd)
            serial_port.flush()
            break

        if request == b'?':
            run_cpu(cpu, play_address, 0, 0, 0)
            serial_port.write([0]) # type=registers
            serial_port.write(memory[0xD400:0xD419])
            serial_port.flush()
            play_calls += 1
            retries = 10
        else:
            print('Board did not send a data request...')
            retries -= 1

    if retries == 0:
        print('Connection timed out')

    serial_port.close()


if __name__ == '__main__':
    parser = ArgumentParser(description='RealSID.py v1.0 - A very rudimentary SID player'+\
                                                 ' for the RealSIDShield (c) 2013 atbrask')

    parser.add_argument('serialport', help='The serial port the Arduino is connected to')
    parser.add_argument('filename', help='Input SID file')
    parser.add_argument('-s', '--song', type=int, default=-1,
                        help='The song number to be played (default is specified in the SID file)')
    parser.add_argument('-t', '--time', type=int, default=-1,
                        help='The desired playtime in seconds (default is forever)')
    parser.add_argument('-b', '--baudrate', type=int, default=115200,
                        help='Specify baudrate (default is 115200)')

    args = parser.parse_args()

    play_sid(args.filename, args.song, args.time, args.serialport, args.baudrate)
