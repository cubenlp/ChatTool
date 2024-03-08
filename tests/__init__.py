"""Unit test package for chattool."""

from chattool import Chat, debug_log
import os

if not os.path.exists('tests'):
    os.mkdir('tests')
if not os.path.exists('tests/testfiles'):
    os.mkdir('tests/testfiles')
