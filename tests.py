import datetime
import pytz
import unittest
from edn_format import edn_lex, edn_parse, \
    loads, dumps, Keyword, Symbol, TaggedElement, add_tag


class ConsoleTest(unittest.TestCase):
    def test_dumping(self):
        is_exception = False
        try:
            loads("[1 true nil]")
        except AttributeError as x:
            is_exception = True
        self.assertFalse(is_exception)


class LexerTest(unittest.TestCase):
    def check_lex(self, lex_input, expected_output):
        lex_output = str(list(edn_lex.lex(lex_input)))
        self.assertEqual(expected_output, lex_output)

    def test_nil(self):
        self.check_lex("nil", "[LexToken(NIL,None,1,0)]")

    def test_boolean(self):
        self.check_lex("true", "[LexToken(BOOLEAN,True,1,0)]")

    def test_integer(self):
        self.check_lex("123", "[LexToken(INTEGER,123,1,0)]")

    def test_keyword(self):
        self.check_lex(r":abc", "[LexToken(KEYWORD,Keyword(abc),1,0)]")
        self.check_lex(r":+", "[LexToken(KEYWORD,Keyword(+),1,0)]")
        self.check_lex(":abc ; a comment",
                       "[LexToken(KEYWORD,Keyword(abc),1,0)]")

    def test_symbol(self):
        self.check_lex("abc", "[LexToken(SYMBOL,Symbol(abc),1,0)]")
        self.check_lex("?abc", "[LexToken(SYMBOL,Symbol(?abc),1,0)]")
        self.check_lex("/", "[LexToken(SYMBOL,Symbol(/),1,0)]")
        self.check_lex("prefix/name",
                       "[LexToken(SYMBOL,Symbol(prefix/name),1,0)]")
        self.check_lex("true.", "[LexToken(SYMBOL,Symbol(true.),1,0)]")
        self.check_lex("$:ABC?", "[LexToken(SYMBOL,Symbol($:ABC?),1,0)]")

    def test_tag(self):
        expected_lex = ("[LexToken(TAG,'inst',1,0), "
                        "LexToken(STRING,'1985-04-12T23:20:50.52Z',1,6)]")
        self.check_lex('#inst "1985-04-12T23:20:50.52Z"', expected_lex)

    def test_char(self):
        self.check_lex(r"\c", "[LexToken(CHAR,'c',1,0)]")

    def test_combined(self):
        combined_lex = ("[LexToken(INTEGER,456,1,0), "
                        "LexToken(NIL,None,1,4), "
                        "LexToken(BOOLEAN,False,1,8)]")
        self.check_lex("456 nil false", combined_lex)

    def test_comment(self):
        self.check_lex("; a comment", "[]")


class ParserTest(unittest.TestCase):
    def check_parse(self, parse_input, expected_output):
        self.assertEqual(expected_output, edn_parse.parse(parse_input))

    def test_numbers(self):
        self.check_parse("1", 1)

    def test_symbol(self):
        self.check_parse('a*b', Symbol("a*b"))

    def test_vector_of_booleans_with_commas(self):
        self.check_parse('[true, false]', [True, False])

    def test_string(self):
        self.check_parse('"ab"', "ab")
        self.check_parse('"blah\n"', "blah\n")
        self.check_parse('"blah\spaceblah"', "blah blah")
        self.check_parse('"blah\n"', "blah\n")

    def test_vector(self):
        self.check_parse("[]", [])
        self.check_parse("[1 2 3]", [1, 2, 3])
        self.check_parse("[1 true nil]", [1, True, None])
        self.check_parse('["abc", "123"]', ["abc", "123"])
        self.check_parse("[:abc 1 true nil]", [Keyword("abc"), 1, True, None])

    def test_set(self):
        self.check_parse("#{}", set())
        self.check_parse("#{1 2 3}", {1, 2, 3})

    def test_list(self):
        self.check_parse("()", tuple())
        self.check_parse("(:abc 1 true nil)", (Keyword("abc"), 1, True, None))

    def test_map(self):
        self.check_parse("{}", {})
        self.check_parse('{"a" [1 2 3]}', {"a": [1, 2, 3]})
        self.check_parse('{"key" "value"}', {"key": "value"})

    def test_char(self):
        self.check_parse(r"\c", "c")

    def test_keyword(self):
        self.check_parse(":abc", Keyword("abc"))

    def test_escapes(self):
        self.check_parse(r"\newline", "\n")
        self.check_parse("\"|\"", "|")
        self.check_parse("\"%\"", "%")


    def test_tag(self):
        self.check_parse(
            '#inst "2012-12-22T19:40:18Z"',
            datetime.datetime(2012, 12, 22, 19, 40, 18, 0, tzinfo=pytz.utc))


class RoundTripTest(unittest.TestCase):
    def check_roundtrip(self, data_input, from_python=False):
        rt_value = (loads(dumps(data_input)) if from_python else
                    dumps(loads(data_input)))
        self.assertEqual(data_input, rt_value)

    def test_nested_quotes(self):
        self.check_roundtrip('nested "quotes"', from_python=True)
        self.assertEqual(loads(dumps('nested "quotes"')),
                         loads(dumps(loads(dumps('nested "quotes"')))))

    def test_set(self):
        self.check_roundtrip({1, 2, 3}, from_python=True)

    def test_combined(self):
        self.check_roundtrip({Keyword("a"): 1,
                              "foo": Keyword("gone"),
                              Keyword("bar"): [1, 2, 3]},
                             from_python=True)

    def test_boolean(self):
        self.check_roundtrip("true")
        self.check_roundtrip("false")

    def test_string(self):
        self.check_roundtrip('"|"')
        self.check_roundtrip('"hello world"')

    def test_keyword(self):
        self.check_roundtrip(":keyword")
        self.check_roundtrip(":+")
        self.check_roundtrip(":!")
        self.check_roundtrip(":-")
        self.check_roundtrip(":_")
        self.check_roundtrip(":$")
        self.check_roundtrip(":&")
        self.check_roundtrip(":=")
        self.check_roundtrip(":.")
        self.check_roundtrip(":abc/def")

    def test_symbol(self):
        self.check_roundtrip("symbol")

    def test_number(self):
        self.check_roundtrip("123")
        self.check_roundtrip("-123")
        self.check_roundtrip("32.23")
        self.check_roundtrip("32.23M")
        self.check_roundtrip("-32.23M")
        self.check_roundtrip("3.23e-10")

    def test_nil(self):
        self.check_roundtrip('nil')

    def test_vector(self):
        self.check_roundtrip('["abc"]')
        self.check_roundtrip('[1]')
        self.check_roundtrip('[1 "abc"]')
        self.check_roundtrip('[1 "abc" true]')
        self.check_roundtrip('[:ghi]')
        self.check_roundtrip('[1 "abc" true :ghi]')

    def test_list(self):
        self.check_roundtrip('(:ghi)')
        self.check_roundtrip('(1 "abc" true :ghi)')

    def test_map(self):
        self.check_roundtrip('{"a" 2}')
        self.check_roundtrip('#{{"a" 1}}')
        self.check_roundtrip('#{{"a" #{{:b 2}}}}')

    def test_tag(self):
        class TagDate(TaggedElement):
            def __init__(self, value):
                self.name = 'date'
                self.value = datetime.datetime.strptime(
                    value,
                    "%d/%m/%Y").date()

            def __str__(self):
                return '#{} "{}"'.format(
                    self.name,
                    self.value.strftime("%d/%m/%Y"))

        add_tag('date', TagDate)
        self.check_roundtrip('#date "19/07/1984"')
        self.check_roundtrip('#inst "1985-04-12T23:20:50Z"')
        self.check_roundtrip('#uuid "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"')


class RoundConversionTripTest(unittest.TestCase):
    def check_roundtrip(self, data_input, expected_value, from_python=False):
        rt_value = (loads(dumps(data_input)) if from_python else
                    dumps(loads(data_input)))
        self.assertEqual(expected_value, rt_value)

    def test_numbers(self):
        self.check_roundtrip("123N", "123")
        self.check_roundtrip("-123N", "-123")
        self.check_roundtrip("+123", "123")
        self.check_roundtrip("+123N", "123")
        self.check_roundtrip("123.2", "123.2")
        self.check_roundtrip("+32.23M", "32.23M")
        self.check_roundtrip("3.23e10", "32300000000.0")

    def test_char(self):
        self.check_roundtrip(r"\c", '"c"')

    def test_vector(self):
        self.check_roundtrip("[ :ghi ]", "[:ghi]")

    def test_discard(self):
        self.check_roundtrip("[:a #_foo 42]", "[:a 42]")


class SetTest(unittest.TestCase):
    def test_set_roundtrip(self):
        rt_value = dumps(loads('#{:a (1 2 3) :b}'))
        possible_vals = ['#{:a (1 2 3) :b}',
                         '#{:a :b (1 2 3)}',
                         '#{(1 2 3) :a :b}',
                         '#{(1 2 3) :b :a}',
                         '#{:b (1 2 3) :a}',
                         '#{:b :a (1 2 3)}']
        self.assertIn(rt_value, possible_vals)


class EdnInstanceTest(unittest.TestCase):
    def test_hashing(self):
        pop_count = len(
            set(map(hash, ["db/id", Keyword("db/id"), Symbol("db/id")])))
        self.assertEqual(pop_count, 3)

    def test_equality(self):
        self.assertTrue("db/id" != Keyword("db/id"))
        self.assertTrue("db/id" != Symbol("db/id"))
        self.assertTrue(Symbol("db/id") != Keyword("db/id"))
        self.assertTrue("db/id" == "db/id")
        self.assertTrue(Keyword("db/id") == Keyword("db/id"))
        self.assertTrue(Symbol("db/id") == Symbol("db/id"))


if __name__ == "__main__":
    unittest.main()
