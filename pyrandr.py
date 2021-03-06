#!/bin/python

# {{ generated_tag }}

from re import search
import argparse
import logging
import math
import subprocess

def fail(message):
    logging.error(message)
    exit(1)

def run(cmd):
    logging.info(cmd)
    subprocess.run(cmd.split(' '))

class Output:
    """
    An xrandr output
    """
    def __init__( self, name, connected, size_x=0, size_y=0, pos_x=0, pos_y=0 ):
        self.name = name
        self.connected = bool(connected)
        self.size_x = int(size_x)
        self.size_y = int(size_y)
        self.pos_x = int(pos_x)
        self.pos_y = int(pos_y)
        self.modes = []

    def get_current_mode( self ):
        """
        return the current resolution of this output
        """
        return next(filter(lambda m: m.current, self.modes), None)

    def get_prefered_mode( self ):
        """
        return the prefered resolution for this output
        """
        return next(filter(lambda m: m.prefered, self.modes), None)

    def get_relative_position( self, other ):
        """
        return the the position of this output relative to the given output
        """
        if self.__is_left_of( other ) and self.__is_right_of( other ):
            return 'center-of'
        if self.__is_above( other ) and self.__is_below( other ):
            return 'center-of'
        if self.__is_left_of( other ):
            return 'left-of'
        if self.__is_right_of( other ):
            return 'right-of'
        if self.__is_above( other ):
            return 'above'
        if self.__is_below( other ):
            return 'below'
        return 'center-of'

    def __get_left( self ):
        return self.pos_x

    def __get_right( self ):
        return self.pos_x + self.size_x

    def __get_top( self ):
        return self.pos_y

    def __get_bottom( self ):
        return self.pos_y + self.size_y

    def __is_left_of( self, output ):
        return self.__get_right() <= output.__get_left()

    def __is_right_of( self, output ):
        return self.__get_left() >= output.__get_right()

    def __is_above( self, output ):
        return self.__get_bottom() <= output.__get_top()

    def __is_below( self, output ):
        return self.__get_top() >= output.__get_bottom()

    def get_scale( self ):
        """
        return the current scale of this output or 1 if this output is not active
        """
        current_mode = self.get_current_mode()
        print(current_mode)
        if current_mode:
            return self.size_x / current_mode.width
        else:
            return 1

    def __str__( self ):
        return "Output %s %s %dx%d+%d+%d (%d modes)" % (self.name, "connected" if self.connected else "disconnected", self.size_x, self.size_y, self.pos_x, self.pos_y, len(self.modes))

class Mode:
    """
    A display mode
    """
    def __init__( self, width, height, prefered=False, current=False ):
        self.width = int(width)
        self.height = int(height)
        self.prefered = prefered
        self.current = current

    def __str__( self ):
        return "Mode %dx%d%s%s" % (self.width, self.height, "*" if self.current else "", "+" if self.prefered else "" )

class XRandr:
    """
    Manages outputs
    """
    def __init__( self ):
        """
        Parses `xrandr` command output
        """
        xrandr_output = subprocess.check_output("xrandr").decode()
        self.outputs = dict()
        self.primary = None

        name = None
        for line in xrandr_output.splitlines():
            logging.debug('xrandr output: %s' % line)

            match = search('^([\w-]+) disconnected ', line)
            if (match):
                name = match.group(1)
                logging.debug('register disconnected output named "%s"' % name)
                self.outputs[name] = Output( name, False)

            match = search('^([\w-]+) connected.* (\d+)x(\d+)\+(\d+)\+(\d+)', line)
            if (match):
                name = match.group(1)
                logging.debug('register connected output named "%s"' % name)
                self.outputs[name] = Output(
                    name,
                    True,
                    match.group(2), match.group(3),
                    match.group(4), match.group(5)
                )
            else:
                match = search('^([\w-]+) connected .*[(]', line)
                if (match):
                    logging.debug('register connected output named "%s"' % name)
                    name = match.group(1)
                    self.outputs[name] = Output(name, True)

            if search(' primary ', line):
                logging.debug('set primary output to "%s"' % name)
                self.primary = name

            match = search('^\s+(\d+)x(\d+)\w?(?:\s+\d+\.\d+)+', line)
            if (match):
               logging.debug('add mode for output named "%s"' % name)
               self.outputs[name].modes.append(Mode(
                    match.group(1),  match.group(2),
                    '+' in line, '*' in line
                ))

    def __primary( self ):
        if not self.primary:
            fail("No primary output detected. See xrandr option --primary.")
        return self.outputs[self.primary]

    def __secondary( self ):
        """
        Find a connected secondary output.
        Returns the output details or `None`.
        """
        secondaries = filter(lambda o: not o == self.__primary(), list(self.outputs.values()))
        connected = filter(lambda o: o.connected, secondaries)
        return next(connected, None)

    def only_laptop( self ):
        self.__turn_on_only( self.__primary().name )

    def only_secondary( self ):
        self.__turn_on_only( self.__secondary().name )

    def __turn_on_only( self, wanted_output ):
        """
        Executes `xrandr` command to turn off all outputs but the given one.
        """
        cmd = "xrandr --output {main} --auto".format(main=wanted_output)
        for output in self.outputs:
            if not output == wanted_output:
                cmd += " --output {name} --off".format(name=output)
        run(cmd)

    def configure( self, position=None, zoom=0 ):
        """
        Configure the connected secondary output:
        - positions the secondary screen
        - apply scale factor
        """
        s = self.__secondary()
        if not position:
            position = s.get_relative_position(self.__primary())
        scale = self.__get_scale_factor(zoom)
        if position in [ 'left-of', 'above' ]:
            self.__position_complex(position, scale)
        elif position in [ 'right-of', 'below' ]:
            self.__position_easy(position, scale)
        elif position == 'center-of':
            self.__position_over_laptop(scale)

    def __get_scale_factor( self, zoom ):
        s = self.__secondary()
        current_scale = 1 if not s else s.get_scale()
        factor = 0.99 if zoom > 0 else 1.01
        new_scale = current_scale
        for i in range(0, abs(zoom)):
            new_scale = new_scale * factor
        return new_scale if new_scale >= 1.01 or new_scale <= 0.99 else 1

    def __position_easy( self, position, scale):
        cmd = "xrandr --output {primary} --auto --output {secondary} --auto --scale {scale}x{scale} --{pos} {primary}".format(
                primary=self.__primary().name,
                secondary=self.__secondary().name,
                scale=scale,
                pos=position
        )
        run(cmd)

    def __position_complex( self, position, scale ):
        p = self.__primary()
        s = self.__secondary()
        s_mode = s.get_current_mode() or s.get_prefered_mode()
        cmd = "xrandr --output {secondary} --auto --scale {scale}x{scale} --pos 0x0 --output {primary} --auto --primary --pos {primary_x}x{primary_y}".format(
                primary=p.name,
                secondary=s.name,
                scale=scale,
                primary_x=int(math.ceil(s_mode.width * scale)) if position == 'left-of' else 0,
                primary_y=int(math.ceil(s_mode.height * scale)) if position == 'above' else 0
        )
        run(cmd)

    def __position_over_laptop( self, scale ):
        p = self.__primary()
        s = self.__secondary()
        s_mode = s.get_current_mode() or s.get_prefered_mode()
        cmd = "xrandr --output {primary} --auto --pos 0x0 --output {secondary} --auto --scale {scale}x{scale} --pos {secondary_x}x{secondary_y}".format(
                primary=p.name,
                secondary=s.name,
                scale=scale,
                secondary_x=int((p.size_x - s_mode.width * scale) / 2),
                secondary_y=int((p.size_y - s_mode.height * scale) / 2)
        )
        run(cmd)

    def log( self ):
        for output in self.outputs.values():
            logging.info( output )
            current_position = output.get_relative_position( self.__primary() )
            logging.debug( "%s position is %s laptop" % (output.name, current_position) )
            for mode in output.modes:
                logging.debug(mode)

    def __str__( self ):
        s = ""
        for name in self.outputs:
            s += "%s\n" % self.outputs[name]
        return s

parser = argparse.ArgumentParser(description='Configure dualscreen')
parser.add_argument("--laptop-only", dest='laptop', action='store_true',
                    help="disable second screen")
parser.add_argument("--external-only", dest='secondary', action='store_true',
                    help="disable laptop")
parser.add_argument("--position",
                    choices=['left-of-laptop', 'right-of-laptop', 'above-laptop', 'below-laptop', 'center-of-laptop'],
                    help="define second screen position relative to laptop")
parser.add_argument("--zoom", type=int, default=0,
                    help="specify zoom factor for second screen (zoom in: 30, zoom out: -30)")
parser.add_argument("--info", action='store_true',
                    help="show current configuration")
parser.add_argument("-v", action='store_true',
                    help="print executed xrandr commands and more")
parser.add_argument("-vv", action='store_true',
                    help="print executed xrandr commands and even more")

args = parser.parse_args()

if args.v:
    logging.basicConfig(level=getattr(logging, 'INFO', None))
if args.vv:
    logging.basicConfig(level=getattr(logging, 'DEBUG', None))

xrandr = XRandr()
xrandr.log()

if args.info:
    exit( 0 )
elif args.laptop:
    xrandr.only_laptop()
elif args.secondary:
    xrandr.only_secondary()
else:
    pos = None
    if args.position:
        pos = args.position[:-7] # remove '-laptop' suffix
    xrandr.configure(pos, args.zoom)
