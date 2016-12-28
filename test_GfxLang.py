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
        self.assertEqual(GetBestType([[-1, 0x7F], [2, 0xFF]]), (12, (12, 4)))
        self.assertEqual(GetBestType([[-1, 0x7F], [2, 0xFFFF]]), (12, (12, 6)))
        self.assertEqual(GetBestType((1, 2, 3)), (13, 1))
        self.assertEqual(GetBestType((-1, 2, 3)), (13, 2))
        self.assertEqual(GetBestType((1, 2, 0x1FF)), (13, 3))
        self.assertEqual(GetBestType((-1, 2, 0xFF)), (13, 4))
        self.assertEqual(GetBestType((-1, 2, 0x1FF)), (13, 4))
    def test_GfxEncodeAsType(self):
        self.assertEqual(EncodeAsType(0x12, 1), [1, 0x12])
        self.assertEqual(EncodeAsType(0x12, 3), [3, 0x12])
        self.assertEqual(EncodeAsType(0x12, 5), [5, 0x12])
        self.assertEqual(EncodeAsType(0x12, 7), [7, 0x12])
        self.assertEqual(EncodeAsType(0x12, 9), [9, 0x12])
        self.assertEqual(EncodeAsType(-128, 2), [2, 128])
        self.assertEqual(EncodeAsType(-32768, 4), [4, 32768])
        self.assertEqual(EncodeAsType(-2**31, 6), [6, 2**31])
        self.assertEqual(EncodeAsType(-2**63, 8), [8, 2**63])
        self.assertEqual(EncodeAsType(-1, 2), [2, 255])
        self.assertEqual(EncodeAsType(-1, 4), [4, 65535])
        self.assertEqual(EncodeAsType(-1, 6), [6, 2**32-1])
        self.assertEqual(EncodeAsType(-1, 8), [8, 2**64-1])
        self.assertEqual(EncodeAsType(b"hello world\n\xb0\x95", 10), [10, b"hello world\n\xb0\x95"])
        self.assertEqual(EncodeAsType(u"hello unicode\xb0", 11), [11, b"hello unicode\xc2\xb0"])
        self.assertEqual(EncodeAsType([1, 2, 3, 4, -1], (12, 4)), [12, [4, [1, 2, 3, 4, 0xFFFF]]])
        self.assertEqual(EncodeAsType([-1, 2, 3, 4, -128], (12, 4)), [12, [4, [0xFFFF, 2, 3, 4, 0xFF80]]])
    def test_GfxTypeDecoder(self):
        self.assertEqual(TypeDecoder([1, 0x12]), 0x12)
        self.assertEqual(TypeDecoder([3, 0x12]), 0x12)
        self.assertEqual(TypeDecoder([5, 0x12]), 0x12)
        self.assertEqual(TypeDecoder([7, 0x12]), 0x12)
        self.assertEqual(TypeDecoder([9, 0x12]), 0x12)
        self.assertEqual(TypeDecoder([2, 128]), -128)
        self.assertEqual(TypeDecoder([4, 32768]), -32768)
        self.assertEqual(TypeDecoder([6, 2**31]), -2**31)
        self.assertEqual(TypeDecoder([8, 2**63]), -2**63)
        self.assertEqual(TypeDecoder([2, 255]), -1)
        self.assertEqual(TypeDecoder([4, 65535]), -1)
        self.assertEqual(TypeDecoder([6, 2**32-1]), -1)
        self.assertEqual(TypeDecoder([8, 2**64-1]), -1)
        self.assertEqual(TypeDecoder([10, b"hello world\n\xb0\x95"]), b"hello world\n\xb0\x95")
        self.assertEqual(TypeDecoder([11, b"hello unicode\xc2\xb0"]), u"hello unicode\xb0")
        self.assertEqual(TypeDecoder([12, [4, [1, 2, 3, 4, 0xFFFF]]]), [1, 2, 3, 4, -1])
        self.assertEqual(TypeDecoder([12, [4, [0xFFFF, 2, 3, 4, 0xFF80]]]), [-1, 2, 3, 4, -128])

