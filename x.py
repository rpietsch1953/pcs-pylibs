#!/usr/bin/env python3
# vim: expandtab:ts=4:sw=4:noai

class w():
    def __init__(self):
        self.a = 3
        self.b = 4

    def x(self):
        n = __class__.__name__
        print(locals())

c = w()
c.x()

