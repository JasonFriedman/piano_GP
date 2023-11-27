#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import enum


class PracticeMode(enum.Enum):
    IDENTITY = enum.auto()
    RIGHT_HAND = enum.auto()
    LEFT_HAND = enum.auto()
    SINGLE_NOTE = enum.auto()
    SLOWER = enum.auto()
