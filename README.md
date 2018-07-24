pyrandr
=======

This wrapper for [xrandr](https://www.x.org/wiki/Projects/XRandR/) aims to provide a simpler CLI.

`xrandr` is a powerful tool to configure X Window System and among others multiple screen systems. I found it too complex for my daily usage so I wrote this wrapper with some assumption:

- I have **one primary output**, and it doesn't change
- sometimes, I need to configure **one single secondary output**, no more
- I want to position this external output relatively to my primary output
- my primary output is HiDPI, I want to scale down the external output when it has a low DPI, and I want the outputs to be correctly positioned
- when my screen is projected, I want to scale up so everyone can see, and I want the outputs to be correctly positioned
- _correctly posisioned_ means to me:
  - not one screen above one part of the other
  - not one screen far away of the other

These requirements should be satisfied with `xrandr`'s `--scale` option, but when I started using this option I was going crazy computing outputs positions. So I wrote this messy code to handle it once and for all.

usage
-----

```
# pyrandr --help
usage: pyrandr.py [-h] [--laptop-only] [--external-only]
                  [--position {left-of-laptop,right-of-laptop,above-laptop,below-laptop,center-of-laptop}]
                  [--zoom ZOOM] [-v] [-vv]

Configure dualscreen

optional arguments:
  -h, --help            show this help message and exit
  --laptop-only         disable second screen
  --external-only       disable laptop
  --position {left-of-laptop,right-of-laptop,above-laptop,below-laptop,center-of-laptop}
                        define second screen position relative to laptop
  --zoom ZOOM           specify zoom factor for second screen (zoom in: 30,
                        zoom out: -30)
  -v                    print executed xrandr commands and more
  -vv                   print executed xrandr commands and even more
```

i3 users
--------

You can take a look to my [i3 configuration](https://github.com/jeremiehuchet/dotfiles/blob/aeb87581eea9f86a6cec6f40d796cd45c829d6c9/roles/desktop_environment/templates/i3/i3.config#L201-L229) to add an _output_ mode `$mod+O` with the following options:

```
Display [L for laptop only, up/down/left/right/C for position, Shift+up/down for zoom]
```
