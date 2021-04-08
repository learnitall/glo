#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
import json
import string
import numpy as np
from glo.readers.file import FileReader, ScrapyJLReader


class TestFileReader:

    class FileReaderTest(FileReader):
        def read(self):
            return "\n".join(self.lines())

    def test_file_reader_finds_abs_path(self, tmpdir):
        """Test that FileReader can resolve relative paths."""

        test_file = tmpdir.mkdir("sub").join("hello.txt")
        test_file.write("hello")

        rel_path = test_file.join("./../../sub/./hello.txt")
        reader = self.FileReaderTest(rel_path)
        assert reader.file_path == test_file.strpath

    def test_file_reader_lines_returns_correct_output(self, tmpdir):
        """Test that FileReader.lines() iterators over file's lines."""

        my_file = """We're no strangers to love
        You know the rules and so do I
        A full commitment's what I'm thinking of
        You wouldn't get this from any other guy
        
        I just wanna tell you how I'm feeling
        Gotta make you understand
        
        Never gonna give you up
        Never gonna let you down
        Never gonna run around and desert you
        Never gonna make you cry
        Never gonna say goodbye
        Never gonna tell a lie and hurt you
        
        We've known each other for so long
        Your heart's been aching, but
        You're too shy to say it
        Inside, we both know what's been going on
        We know the game and we're gonna play it
        
        And if you ask me how I'm feeling
        Don't tell me you're too blind to see
        
        Never gonna give you up
        Never gonna let you down
        Never gonna run around and desert you
        Never gonna make you cry
        Never gonna say goodbye
        Never gonna tell a lie and hurt you
        
        Never gonna give you up
        Never gonna let you down
        Never gonna run around and desert you
        Never gonna make you cry
        Never gonna say goodbye
        Never gonna tell a lie and hurt you
        
        (Ooh, give you up)
        (Ooh, give you up)
        Never gonna give, never gonna give
        (Give you up)
        Never gonna give, never gonna give
        (Give you up)
        
        We've known each other for so long
        Your heart's been aching, but
        You're too shy to say it
        Inside, we both know what's been going on
        We know the game and we're gonna play it
        
        I just wanna tell you how I'm feeling
        Gotta make you understand
        
        Never gonna give you up
        Never gonna let you down
        Never gonna run around and desert you
        Never gonna make you cry
        Never gonna say goodbye
        Never gonna tell a lie and hurt you
        
        Never gonna give you up
        Never gonna let you down
        Never gonna run around and desert you
        Never gonna make you cry
        Never gonna say goodbye
        Never gonna tell a lie and hurt you
        
        Never gonna give you up
        Never gonna let you down
        Never gonna run around and desert you
        Never gonna make you cry
        Never gonna say goodbye
        Never gonna tell a lie and hurt you
        """

        p = tmpdir.join("rick.text")
        p.write(my_file)

        reader = self.FileReaderTest(p.strpath)
        assert list(reader.lines()) == \
               list([l.strip().encode("latin-1") for l in my_file.split("\n")])

def test_scrapy_jl_reader_loads_json(tmpdir):
    """Test that ScrapyJLReader can load JSON from file."""

    p = tmpdir.join("json.jl")
    rand_ints = np.random.randint(1, 100, 15)
    rand_strs = np.random.choice(list(string.printable), 15)
    data = [{"data": int(i), "strs": str(s)} for i, s in
            zip(rand_ints, rand_strs)]
    file_data = "\n".join([json.dumps(line) for line in data])
    p.write(file_data)

    reader = ScrapyJLReader(p.strpath)
    data_set = reader.read()
    assert sorted(list(data_set.frame.data)) == sorted(list(rand_ints))
    assert sorted(list(data_set.frame.strs)) == sorted(list(rand_strs))
