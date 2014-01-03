# -*- coding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from unittest import TestCase

import ujson
try:
    import json
except ImportError:
    import simplejson as json
import array
import math
import platform
import sys
import time
import datetime
import calendar
import StringIO
import re
import random
import decimal
from functools import partial

PY3 = (sys.version_info[0] >= 3)

def _python_ver(skip_major, skip_minor=None):
    major, minor = sys.version_info[:2]
    return major == skip_major and (skip_minor is None or minor == skip_minor)

json_unicode = (json.dumps if sys.version_info[0] >= 3
                else partial(json.dumps, encoding="utf-8"))

class UltraJSONTests(TestCase):

    def test_encodeDecimal(self):
        sut = decimal.Decimal("1337.1337")
        encoded = ujson.encode(sut, double_precision=100)
        decoded = ujson.decode(encoded)
        self.assertEquals(decoded, 1337.1337)

    def test_encodeStringConversion(self):
        input = "A string \\ / \b \f \n \r \t </script> &"
        not_html_encoded = '"A string \\\\ \\/ \\b \\f \\n \\r \\t <\\/script> &"'
        html_encoded = '"A string \\\\ \\/ \\b \\f \\n \\r \\t \\u003c\\/script\\u003e \\u0026"'

        def helper(expected_output, **encode_kwargs):
            output = ujson.encode(input, **encode_kwargs)
            self.assertEquals(input, json.loads(output))
            self.assertEquals(output, expected_output)
            self.assertEquals(input, ujson.decode(output))

        # Default behavior assumes encode_html_chars=False.
        helper(not_html_encoded, ensure_ascii=True)
        helper(not_html_encoded, ensure_ascii=False)

        # Make sure explicit encode_html_chars=False works.
        helper(not_html_encoded, ensure_ascii=True, encode_html_chars=False)
        helper(not_html_encoded, ensure_ascii=False, encode_html_chars=False)

        # Make sure explicit encode_html_chars=True does the encoding.
        helper(html_encoded, ensure_ascii=True, encode_html_chars=True)
        helper(html_encoded, ensure_ascii=False, encode_html_chars=True)

    def testWriteEscapedString(self):
        self.assertEqual('"\\u003cimg src=\'\\u0026amp;\'\\/\\u003e"', ujson.dumps("<img src='&amp;'/>", encode_html_chars=True))

    def test_doubleLongIssue(self):
        sut = {u'a': -4342969734183514}
        encoded = json.dumps(sut)
        decoded = json.loads(encoded)
        self.assertEqual(sut, decoded)
        encoded = ujson.encode(sut, double_precision=100)
        decoded = ujson.decode(encoded)
        self.assertEqual(sut, decoded)

    def test_doubleLongDecimalIssue(self):
        sut = {u'a': -12345678901234.56789012}
        encoded = json.dumps(sut)
        decoded = json.loads(encoded)
        self.assertEqual(sut, decoded)
        encoded = ujson.encode(sut, double_precision=100)
        decoded = ujson.decode(encoded)
        self.assertEqual(sut, decoded)

    def test_encodeDecodeLongDecimal(self):
        sut = {u'a': -528656961.4399388}
        encoded = ujson.dumps(sut, double_precision=15)
        ujson.decode(encoded)

    def test_decimalDecodeTest(self):
        sut = {u'a': 4.56}
        encoded = ujson.encode(sut)
        decoded = ujson.decode(encoded)
        self.assertNotEqual(sut, decoded)

    def test_decimalDecodeTestPrecise(self):
        sut = {u'a': 4.56}
        encoded = ujson.encode(sut)
        decoded = ujson.decode(encoded, precise_float=True)
        self.assertEqual(sut, decoded)

    def test_encodeDictWithUnicodeKeys(self):
        input = { u"key1": u"value1", u"key1": u"value1", u"key1": u"value1", u"key1": u"value1", u"key1": u"value1", u"key1": u"value1" }
        output = ujson.encode(input)

        input = { u"بن": u"value1", u"بن": u"value1", u"بن": u"value1", u"بن": u"value1", u"بن": u"value1", u"بن": u"value1", u"بن": u"value1" }
        output = ujson.encode(input)

    def test_encodeDoubleConversion(self):
        input = math.pi
        output = ujson.encode(input)
        self.assertEquals(round(input, 5), round(json.loads(output), 5))
        self.assertEquals(round(input, 5), round(ujson.decode(output), 5))

    def test_encodeWithDecimal(self):
        input = 1.0
        output = ujson.encode(input)
        self.assertEquals(output, "1.0")

    def test_encodeDoubleNegConversion(self):
        input = -math.pi
        output = ujson.encode(input)

        self.assertEquals(round(input, 5), round(json.loads(output), 5))
        self.assertEquals(round(input, 5), round(ujson.decode(output), 5))

    def test_encodeArrayOfNestedArrays(self):
        input = [[[[]]]] * 20
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        #self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeArrayOfDoubles(self):
        input = [ 31337.31337, 31337.31337, 31337.31337, 31337.31337] * 10
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        #self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

    def test_doublePrecisionTest(self):
        input = 30.012345678901234
        output = ujson.encode(input, double_precision = 15)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(input, ujson.decode(output))

        output = ujson.encode(input, double_precision = 9)
        self.assertEquals(round(input, 9), json.loads(output))
        self.assertEquals(round(input, 9), ujson.decode(output))

        output = ujson.encode(input, double_precision = 3)
        self.assertEquals(round(input, 3), json.loads(output))
        self.assertEquals(round(input, 3), ujson.decode(output))

    def test_invalidDoublePrecision(self):
        input = 30.12345678901234567890
        output = ujson.encode(input, double_precision = 20)
        # should snap to the max, which is 15
        self.assertEquals(round(input, 15), json.loads(output))
        self.assertEquals(round(input, 15), ujson.decode(output))

        output = ujson.encode(input, double_precision = -1)
        # also should snap to the max, which is 15
        self.assertEquals(round(input, 15), json.loads(output))
        self.assertEquals(round(input, 15), ujson.decode(output))

        # will throw typeError
        self.assertRaises(TypeError, ujson.encode, input, double_precision = '9')
        # will throw typeError
        self.assertRaises(TypeError, ujson.encode, input, double_precision = None)

    def test_encodeStringConversion(self):
        input = "A string \\ / \b \f \n \r \t"
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, '"A string \\\\ \\/ \\b \\f \\n \\r \\t"')
        self.assertEquals(input, ujson.decode(output))

    def test_decodeUnicodeConversion(self):
        pass

    def test_encodeUnicodeConversion1(self):
        input = "Räksmörgås اسامة بن محمد بن عوض بن لادن"
        enc = ujson.encode(input)
        dec = ujson.decode(enc)
        self.assertEquals(enc, json_unicode(input))
        self.assertEquals(dec, json.loads(enc))

    def test_encodeControlEscaping(self):
        input = "\x19"
        enc = ujson.encode(input)
        dec = ujson.decode(enc)
        self.assertEquals(input, dec)
        self.assertEquals(enc, json_unicode(input))

    def test_encodeUnicodeConversion2(self):
        input = "\xe6\x97\xa5\xd1\x88"
        enc = ujson.encode(input)
        dec = ujson.decode(enc)
        self.assertEquals(enc, json_unicode(input))
        self.assertEquals(dec, json.loads(enc))

    def test_encodeUnicodeSurrogatePair(self):
        input = "\xf0\x90\x8d\x86"
        enc = ujson.encode(input)
        dec = ujson.decode(enc)

        self.assertEquals(enc, json_unicode(input))
        self.assertEquals(dec, json.loads(enc))

    def test_encodeUnicode4BytesUTF8(self):
        input = "\xf0\x91\x80\xb0TRAILINGNORMAL"
        enc = ujson.encode(input)
        dec = ujson.decode(enc)

        self.assertEquals(enc, json_unicode(input))
        self.assertEquals(dec, json.loads(enc))

    def test_encodeUnicode4BytesUTF8Highest(self):
        input = "\xf3\xbf\xbf\xbfTRAILINGNORMAL"
        enc = ujson.encode(input)
        dec = ujson.decode(enc)

        self.assertEquals(enc, json_unicode(input))
        self.assertEquals(dec, json.loads(enc))

    # From http://www.ietf.org/rfc/rfc4627.txt #2.5
    # "To escape an extended character that is not in the Basic Multilingual
    # Plane, the character is represented as a twelve-character sequence,
    # encoding the UTF-16 surrogate pair."
    #
    # Testing that character outside of BMP, represented as \UXXXXXXXX in
    # python is correctly encoded as \uXXXX\uXXXX in json.
    def testEncodeUnicodeBMP(self):
        s = u'\U0001f42e\U0001F42D\U0001F435\U0001F41A'
        encoded = ujson.dumps(s)
        encoded_json = json.dumps(s)
        self.assertEqual(len(encoded), len(s) * 12 + 2) # 12 characters + quotes
        self.assertEqual(encoded, encoded_json)
        decoded = ujson.loads(encoded)
        self.assertEqual(s, decoded)

        # ujson outputs an UTF-8 encoded str object
        encoded = ujson.dumps(s, ensure_ascii=False).decode("utf-8")
        # json outputs an unicode object
        encoded_json = json.dumps(s, ensure_ascii=False)
        self.assertEqual(len(encoded), len(s) + 2) # original length + quotes
        self.assertEqual(encoded, encoded_json)
        decoded = ujson.loads(encoded)
        self.assertEqual(s, decoded)

    def testEncodeSymbols(self):
        s = u'\u273f\u2661\u273f'
        encoded = ujson.dumps(s)
        encoded_json = json.dumps(s)
        self.assertEqual(len(encoded), len(s) * 6 + 2) # 6 characters + quotes
        self.assertEqual(encoded, encoded_json)
        decoded = ujson.loads(encoded)
        self.assertEqual(s, decoded)

        # ujson outputs an UTF-8 encoded str object
        encoded = ujson.dumps(s, ensure_ascii=False).decode("utf-8")
        # json outputs an unicode object
        encoded_json = json.dumps(s, ensure_ascii=False)
        self.assertEqual(len(encoded), len(s) + 2) # original length + quotes
        self.assertEqual(encoded, encoded_json)
        decoded = ujson.loads(encoded)
        self.assertEqual(s, decoded)

    def test_encodeArrayInArray(self):
        input = [[[[]]]]
        output = ujson.encode(input)

        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeIntConversion(self):
        input = 31337
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeIntNegConversion(self):
        input = -31337
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeLongNegConversion(self):
        input = -9223372036854775808
        output = ujson.encode(input)

        outputjson = json.loads(output)
        outputujson = ujson.decode(output)

        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeListConversion(self):
        input = [ 1, 2, 3, 4 ]
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeDictConversion(self):
        input = { "k1": 1, "k2":  2, "k3": 3, "k4": 4 }
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(input, ujson.decode(output))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeNoneConversion(self):
        input = None
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeTrueConversion(self):
        input = True
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeFalseConversion(self):
        input = False
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeDatetimeConversion(self):
        ts = time.time()
        input = datetime.datetime.fromtimestamp(ts)
        output = ujson.encode(input)
        expected = calendar.timegm(input.utctimetuple())
        self.assertEquals(int(expected), json.loads(output))
        self.assertEquals(int(expected), ujson.decode(output))

    def test_encodeDateConversion(self):
        ts = time.time()
        input = datetime.date.fromtimestamp(ts)

        output = ujson.encode(input)
        tup = ( input.year, input.month, input.day, 0, 0, 0 )

        expected = calendar.timegm(tup)
        self.assertEquals(int(expected), json.loads(output))
        self.assertEquals(int(expected), ujson.decode(output))

    def test_encodeToUTF8(self):
        input = "\xe6\x97\xa5\xd1\x88"
        enc = ujson.encode(input, ensure_ascii=False)
        dec = ujson.decode(enc)
        self.assertEquals(enc, json_unicode(input, ensure_ascii=False))
        self.assertEquals(dec, json.loads(enc))

    def test_decodeFromUnicode(self):
        input = u"{\"obj\": 31337}"
        dec1 = ujson.decode(input)
        dec2 = ujson.decode(str(input))
        self.assertEquals(dec1, dec2)

    def test_encodeDoubleNan(self):
        input = float('nan')
        self.assertRaises(OverflowError, ujson.encode, input)

    def test_encodeDoubleInf(self):
        input = float('inf')
        self.assertRaises(OverflowError, ujson.encode, input)

    def test_encodeDoubleNegInf(self):
        input = -float('inf')
        self.assertRaises(OverflowError, ujson.encode, input)

    def test_decodeJibberish(self):
        input = "fdsa sda v9sa fdsa"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeBrokenArrayStart(self):
        input = "["
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeBrokenObjectStart(self):
        input = "{"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeBrokenArrayEnd(self):
        input = "]"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeArrayDepthTooBig(self):
        input = '[' * (1024 * 1024)
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeBrokenObjectEnd(self):
        input = "}"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeObjectDepthTooBig(self):
        input = '{' * (1024 * 1024)
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeStringUnterminated(self):
        input = "\"TESTING"
        self.assertRaises(ValueError, ujson.decode, input)
    def test_decodeStringUntermEscapeSequence(self):
        input = "\"TESTING\\\""
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeStringBadEscape(self):
        input = "\"TESTING\\\""
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeTrueBroken(self):
        input = "tru"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeFalseBroken(self):
        input = "fa"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeNullBroken(self):
        input = "n"
        self.assertRaises(ValueError, ujson.decode, input)


    def test_decodeBrokenDictKeyTypeLeakTest(self):
        input = '{{1337:""}}'
        for x in xrange(1000):
            try:
                ujson.decode(input)
                assert False, "Expected exception!"
            except(ValueError),e:
                continue

            assert False, "Wrong exception"

    def test_decodeBrokenDictLeakTest(self):
        input = '{{"key":"}'
        for x in xrange(1000):
            self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeBrokenListLeakTest(self):
        input = '[[[true'
        for x in xrange(1000):
            self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeDictWithNoKey(self):
        input = "{{{{31337}}}}"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeDictWithNoColonOrValue(self):
        input = "{{{{\"key\"}}}}"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeDictWithNoValue(self):
        input = "{{{{\"key\":}}}}"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeNumericIntPos(self):
        input = "31337"
        self.assertEquals (31337, ujson.decode(input))

    def test_decodeNumericIntNeg(self):
        input = "-31337"
        self.assertEquals (-31337, ujson.decode(input))

    #@unittest.skipIf(_python_ver(3), "No exception in Python 3")
    def test_encodeUnicode4BytesUTF8Fail(self):
        input = "\xfd\xbf\xbf\xbf\xbf\xbf"
        self.assertRaises(OverflowError, ujson.encode, input)

    def test_encodeNullCharacter(self):
        input = "31337 \x00 1337"
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

        input = "\x00"
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

        self.assertEquals('"  \\u0000\\r\\n "', ujson.dumps(u"  \u0000\r\n "))

    def test_decodeNullCharacter(self):
        input = "\"31337 \\u0000 31337\""
        self.assertEquals(ujson.decode(input), json.loads(input))

    def test_encodeListLongConversion(self):
        input = [9223372036854775807, 9223372036854775807, 9223372036854775807,
                 9223372036854775807, 9223372036854775807, 9223372036854775807 ]
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(input, ujson.decode(output))

    def test_encodeLongConversion(self):
        input = 9223372036854775807
        output = ujson.encode(input)
        self.assertEquals(input, json.loads(output))
        self.assertEquals(output, json.dumps(input))
        self.assertEquals(input, ujson.decode(output))

    def test_numericIntExp(self):
        input = "1337E40"
        output = ujson.decode(input)
        self.assertEquals(output, json.loads(input))

    def test_numericIntFrcExp(self):
        input = "1.337E40"
        output = ujson.decode(input)
        self.assertEquals(output, json.loads(input))

    def test_decodeNumericIntExpEPLUS(self):
        input = "1337E+9"
        output = ujson.decode(input)
        self.assertEquals(output, json.loads(input))

    def test_decodeNumericIntExpePLUS(self):
        input = "1.337e+40"
        output = ujson.decode(input)
        self.assertEquals(output, json.loads(input))

    def test_decodeNumericIntExpE(self):
        input = "1337E40"
        output = ujson.decode(input)
        self.assertEquals(output, json.loads(input))

    def test_decodeNumericIntExpe(self):
        input = "1337e40"
        output = ujson.decode(input)
        self.assertEquals(output, json.loads(input))

    def test_decodeNumericIntExpEMinus(self):
        input = "1.337E-4"
        output = ujson.decode(input)
        self.assertEquals(output, json.loads(input))

    def test_decodeNumericIntExpeMinus(self):
        input = "1.337e-4"
        output = ujson.decode(input)
        self.assertEquals(output, json.loads(input))

    def test_dumpToFile(self):
        f = StringIO.StringIO()
        ujson.dump([1, 2, 3], f)
        self.assertEquals("[1,2,3]", f.getvalue())

    def test_dumpToFileLikeObject(self):
        class filelike:
            def __init__(self):
                self.bytes = ''
            def write(self, bytes):
                self.bytes += bytes
        f = filelike()
        ujson.dump([1, 2, 3], f)
        self.assertEquals("[1,2,3]", f.bytes)

    def test_dumpFileArgsError(self):
        try:
            ujson.dump([], '')
        except TypeError:
            pass
        else:
            assert False, 'expected TypeError'

    def test_loadFile(self):
        f = StringIO.StringIO("[1,2,3,4]")
        self.assertEquals([1, 2, 3, 4], ujson.load(f))

    def test_loadFileLikeObject(self):
        class filelike:
            def read(self):
                try:
                    self.end
                except AttributeError:
                    self.end = True
                    return "[1,2,3,4]"
        f = filelike()
        self.assertEquals([1, 2, 3, 4], ujson.load(f))

    def test_loadFileArgsError(self):
        try:
            ujson.load("[]")
        except TypeError:
            pass
        else:
            assert False, "expected TypeError"

    def test_version(self):
        assert re.match(r'^\d+\.\d+(\.\d+)?$', ujson.__version__), \
               "ujson.__version__ must be a string like '1.4.0'"

    def test_encodeNumericOverflow(self):
        if ujson.bigint_supported:
            ujson.encode(12839128391289382193812939)
        else:
          self.assertRaises(OverflowError, ujson.encode, 12839128391289382193812939)

    def test_decodeNumberWith32bitSignBit(self):
        # Test that numbers that fit within 32 bits but would have the
        # sign bit set (2**31 <= x < 2**32) are decoded properly.
        boundary1 = 2**31
        boundary2 = 2**32
        docs = (
            '{"id": 3590016419}',
            '{"id": %s}' % 2**31,
            '{"id": %s}' % 2**32,
            '{"id": %s}' % ((2**32)-1),
        )
        results = (3590016419, 2**31, 2**32, 2**32-1)
        for doc,result in zip(docs, results):
            self.assertEqual(ujson.decode(doc)['id'], result)

    def test_encodeBigEscape(self):
        for x in xrange(10):
            if PY3:
                base = '\u00e5'.encode('utf-8')
            else:
                base = "\xc3\xa5"
            input = base * 1024 * 1024 * 2
            output = ujson.encode(input)

    def test_decodeBigEscape(self):
        for x in xrange(10):
            if PY3:
                base = '\u00e5'.encode('utf-8')
                quote = "\"".encode()
            else:
                base = "\xc3\xa5"
                quote = "\""
            input = quote + (base * 1024 * 1024 * 2) + quote
            output = ujson.decode(input)

    def test_toDict(self):
        d = {u"key": 31337}

        class DictTest:
            def toDict(self):
                return d

        o = DictTest()
        output = ujson.encode(o)
        dec = ujson.decode(output)
        self.assertEquals(dec, d)

    def test_decodeArrayTrailingCommaFail(self):
        input = "[31337,]"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeArrayLeadingCommaFail(self):
        input = "[,31337]"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeArrayOnlyCommaFail(self):
        input = "[,]"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeArrayUnmatchedBracketFail(self):
        input = "[]]"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeArrayEmpty(self):
        input = "[]"
        obj = ujson.decode(input)
        self.assertEqual([], obj)

    def test_decodeArrayDict(self):
        input = "{}"
        obj = ujson.decode(input)
        self.assertEqual({}, obj)

    def test_decodeArrayOneItem(self):
        input = "[31337]"
        ujson.decode(input)

    def test_decodeBigValue(self):
        input = "9223372036854775807"
        ujson.decode(input)

    def test_decodeSmallValue(self):
        input = "-9223372036854775808"
        ujson.decode(input)

    def test_decodeTooBigValue(self):
        if ujson.bigint_supported:
            for i in range(30):
                input = 9223372036854775800 + i
                obj = ujson.decode('%s' % input)
                self.assertEqual(input, obj)
            for i in range(30):
                input = 41255008296960273580 + i
                obj = ujson.decode('%s' % input)
                self.assertEqual(input, obj)
        else:
          try:
              input = "9223372036854775808"
              ujson.decode(input)
          except ValueError, e:
              pass
          else:
              assert False, "expected ValueError"

    def test_decodeTooBigValueOver64Characters(self):
      if not ujson.bigint_supported:
        return
      # ujson bignum support has two paths for decoding
      # One for strings with length < 64 characters with a local buffer(fast)
      # And one for length >= 64 with memory allocation (slower)
      input = '1234567890' * 100 # 1000 characters
      obj = ujson.decode(input)
      self.assertEqual(long(input), obj)

    def test_decodeTooBigValueFloat(self):
        if ujson.bigint_supported:
            for i in range(30):
              input = '%s.9' % (9223372036854775800 + i)
              obj = ujson.decode(input)
              self.assertEqual(float(input), obj)
        else:
          input = "9223372036854775808.9"
          self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeTooSmallValue(self):
        if ujson.bigint_supported:
            for i in range(30):
                input = -90223372036854775809 - i
                obj = ujson.decode('%s' % input)
                self.assertEqual(input, obj)
            for i in range(30):
                input = -41255008296960273580 - i
                obj = ujson.decode('%s' % input)
                self.assertEqual(input, obj)
        else:
          input = "-90223372036854775809"
          self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeTooSmallValueFloat(self):
        if ujson.bigint_supported:
            for i in range(30):
              input = '-%s.9' % (9223372036854775800 + i)
              obj = ujson.decode(input)
              self.assertEqual(float(input), obj)
        else:
          input = "9223372036854775808.9"
          self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeWithTrailingWhitespaces(self):
        input = "{}\n\t "
        ujson.decode(input)

    def test_decodeWithTrailingNonWhitespaces(self):
        input = "{}\n\t a"
        self.assertRaises(ValueError, ujson.decode, input)

    def test_decodeArrayWithBigInt(self):
        if ujson.bigint_supported:
            input = 18446098363113800555
            self.assertEquals(ujson.loads('[%s]' % input), [input])
        else:
          self.assertRaises(ValueError, ujson.loads, '[18446098363113800555]')

    def test_decodeFloatingPointAdditionalTests(self):
        self.assertEquals(-1.1234567893, ujson.loads("-1.1234567893"))
        self.assertEquals(-1.234567893, ujson.loads("-1.234567893"))
        self.assertEquals(-1.34567893, ujson.loads("-1.34567893"))
        self.assertEquals(-1.4567893, ujson.loads("-1.4567893"))
        self.assertEquals(-1.567893, ujson.loads("-1.567893"))
        self.assertEquals(-1.67893, ujson.loads("-1.67893"))
        self.assertEquals(-1.7893, ujson.loads("-1.7893"))
        self.assertEquals(-1.893, ujson.loads("-1.893"))
        self.assertEquals(-1.3, ujson.loads("-1.3"))

        self.assertEquals(1.1234567893, ujson.loads("1.1234567893"))
        self.assertEquals(1.234567893, ujson.loads("1.234567893"))
        self.assertEquals(1.34567893, ujson.loads("1.34567893"))
        self.assertEquals(1.4567893, ujson.loads("1.4567893"))
        self.assertEquals(1.567893, ujson.loads("1.567893"))
        self.assertEquals(1.67893, ujson.loads("1.67893"))
        self.assertEquals(1.7893, ujson.loads("1.7893"))
        self.assertEquals(1.893, ujson.loads("1.893"))
        self.assertEquals(1.3, ujson.loads("1.3"))

    def test_encodeBigSet(self):
        s = set()
        for x in xrange(0, 100000):
            s.add(x)
        ujson.encode(s)

    def test_encodeEmptySet(self):
        s = set()
        self.assertEquals("[]", ujson.encode(s))

    def test_encodeSet(self):
        s = set([1,2,3,4,5,6,7,8,9])
        enc = ujson.encode(s)
        dec = ujson.decode(enc)

        for v in dec:
            self.assertTrue(v in s)

    def test_readBadObjectSyntax(self):
        self.assertRaises(ValueError, ujson.loads, '{"age", 44}')

    def test_readTrue(self):
        self.assertEqual(True, ujson.loads("true"))

    def test_readFalse(self):
        self.assertEqual(False, ujson.loads("false"))

    def test_readNull(self):
        self.assertEqual(None, ujson.loads("null"))

    def test_writeTrue(self):
        self.assertEqual("true", ujson.dumps(True))

    def test_writeFalse(self):
        self.assertEqual("false", ujson.dumps(False))

    def test_writeNull(self):
        self.assertEqual("null", ujson.dumps(None))

    def test_readArrayOfSymbols(self):
        self.assertEqual([True, False, None], ujson.loads(" [ true, false,null] "))

    def test_writeArrayOfSymbolsFromList(self):
        self.assertEqual("[true,false,null]", ujson.dumps([True, False, None]))

    def test_writeArrayOfSymbolsFromTuple(self):
        self.assertEqual("[true,false,null]", ujson.dumps((True, False, None)))

    # Ensure that ujson can digest both unicode objects and utf-8 strings
    def test_encodeUTF8EncodedString(self):
        unicode_str = u"مرحبا العالم Salam dünya Прывітанне свет Здравей, свят"
        utf_str = unicode_str.encode('utf-8')

        encoded_from_unicode = ujson.encode(unicode_str)
        encoded_from_utf_str = ujson.encode(utf_str)

        self.assertEqual(encoded_from_unicode, encoded_from_utf_str)

        encoded_from_unicode = ujson.encode(unicode_str, ensure_ascii=False)
        encoded_from_utf_str = ujson.encode(utf_str, ensure_ascii=False)

        self.assertEqual(encoded_from_unicode, encoded_from_utf_str)

    def test_functionReferenceEncoding(self):
        def func(): pass
        self.assertRaises(TypeError, ujson.dumps, {'func': func})

    def test_moduleEncoding(self):
        self.assertRaises(TypeError, ujson.dumps, {'module': array})

    def test_classEncoding(self):
        class Test():
          pass
        self.assertRaises(TypeError, ujson.dumps, {'class': Test})

    def test_classInstanceEncoding(self):
        class Test():
          pass
        self.assertRaises(TypeError, ujson.dumps, {'class': Test()})

    def test_callableReferenceEncoding(self):
        class CallableClass:
          def __call__(self):
            return True
        callable_instance = CallableClass()
        self.assertRaises(TypeError, ujson.dumps, {'inst': callable_instance})

    def test_arrayInstanceEncoding(self):
        arr = array.array('i', [1,2,3])
        self.assertRaises(TypeError, ujson.dumps, {'array_inst': arr})


if __name__ == "__main__":
    unittest.main()