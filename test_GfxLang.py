from unittest import TestCase
from GfxLang import *

class TestGfxCompiler(TestCase):
    def test_ForthParse(self):
        Tokens = ForthParse(
            "1 @1$%^& 'hello spaces' #__NAME_   $hello 1+2 \"hi  there\"")
        self.assertListEqual(
            Tokens, [
                "1", "@1$%^&", "'hello spaces'", "#__NAME_", "$hello", "1+2", "\"hi  there\""])
    def test_GfxCompile(self):
        Program = "-1 2 3 $add$ $mul$ 3 4 $swap$ $sub$"
        Mine = GfxCompiler(Program)
        self.assertListEqual(
            Mine.CmdList,
            [(False, -1),
             (False, 2),
             (False, 3),
             (True, GFX_CMD_ADD),
             (True, GFX_CMD_MUL),
             (False, 3),
             (False, 4),
             (True, GFX_CMD_SWAP),
             (True, GFX_CMD_SUB)])
    def test_GfxExec(self):
        Program = "-1 2 3 $add$ $mul$ 3 4 $swap$ $sub$"
        Mine = GfxCompiler(Program)
        self.assertListEqual(
            Mine.Exec({}),
            [-1*(2+3), 4-3])
    def test_GfxGetBestType(self):
        self.assertEqual(GetBestType(None), 0)
        self.assertEqual(GetBestType(()), 0)
        self.assertEqual(GetBestType([]), 0)
        self.assertEqual(GetBestType(0), 1)
        self.assertEqual(GetBestType(-1), 2)
        self.assertEqual(GetBestType(-128), 2)
        self.assertEqual(GetBestType(0xFF), 1)
        self.assertEqual(GetBestType(0x100), 3)
        self.assertEqual(GetBestType(0xFFFF), 3)
        self.assertEqual(GetBestType(-32768), 4)
        self.assertEqual(GetBestType(0x10000), 5)
        self.assertEqual(GetBestType(0xFFFFFF), 5)
        self.assertEqual(GetBestType(0xFFFFFFFF), 5)
        self.assertEqual(GetBestType(-2 ** 16), 6)
        self.assertEqual(GetBestType(-2 ** 23), 6)
        self.assertEqual(GetBestType(-2 ** 31), 6)
        self.assertEqual(GetBestType(0x100000000), 7)
        self.assertEqual(GetBestType(0xFFFFFFFFFFFF), 7)
        self.assertEqual(GetBestType(0xFFFFFFFFFFFFFFFF), 7)
        self.assertEqual(GetBestType(-2 ** 32), 8)
        self.assertEqual(GetBestType(-2 ** 47), 8)
        self.assertEqual(GetBestType(-2 ** 63), 8)
        self.assertEqual(GetBestType(2 ** 64), 9)
        self.assertEqual(GetBestType(2 ** 96), 9)
        self.assertEqual(GetBestType(2 ** 127), 9)
        self.assertEqual(GetBestType(b""), 10)
        self.assertEqual(GetBestType(b"hello"), 10)
        self.assertEqual(GetBestType(b"\xc2\xb0"), 10)
        self.assertEqual(GetBestType(b"\0test\0"), 10)
        self.assertEqual(GetBestType(u""), 11)
        self.assertEqual(GetBestType(u"hello"), 11)
        self.assertEqual(GetBestType(u"\xb0"), 11)
        self.assertEqual(GetBestType(u"\u2022 hi there"), 11)
        self.assertEqual(GetBestType([1, 2, 3]), (12, 1))
        self.assertEqual(GetBestType([-1, 2, 3]), (12, 2))
        self.assertEqual(GetBestType([1, 2, 0x1FF]), (12, 3))
        self.assertEqual(GetBestType([-1, 2, 0xFF]), (12, 4))
        self.assertEqual(GetBestType([-1, 2, 0x1FF]), (12, 4))
        self.assertEqual(GetBestType((1, 2, 3)), (13, 1))
        self.assertEqual(GetBestType((-1, 2, 3)), (13, 2))
        self.assertEqual(GetBestType((1, 2, 0x1FF)), (13, 3))
        self.assertEqual(GetBestType((-1, 2, 0xFF)), (13, 4))
        self.assertEqual(GetBestType((-1, 2, 0x1FF)), (13, 4))
