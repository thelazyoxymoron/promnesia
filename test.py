#!/usr/bin/env python3.6
from os.path import join, getsize
from pathlib import Path
from tempfile import TemporaryDirectory

from pytest import mark # type: ignore
skip = mark.skip

from wereyouhere.common import History
from wereyouhere.render import render


def test_takeout():
    test_takeout_dir = "testdata/takeout"
    import wereyouhere.generator.takeout as takeout_gen
    histories = takeout_gen.get_takeout_histories(test_takeout_dir)
    [hist] = histories
    assert len(hist) > 0 # kinda arbitrary?

    with TemporaryDirectory() as tdir:
        render([hist], join(tdir, 'res.json'))

def test_chrome():
    import wereyouhere.generator.chrome as chrome_gen
    import imp
    backup_db = imp.load_source('hdb', 'scripts/backup-chrome-history-db.py')

    with TemporaryDirectory() as tdir:
        backup_db.backup_to(tdir)

        [hist] = list(chrome_gen.iter_chrome_histories(tdir))
        assert len(hist) > 10 # kinda random sanity check

        render([hist], join(tdir, 'res.json'))

def test_plaintext_path_extractor():
    import wereyouhere.generator.custom as custom_gen
    from wereyouhere.generator.plaintext import extract_from_path

    hist = custom_gen.get_custom_history(
        extract_from_path('testdata/custom'),
    )
    assert len(hist) == 5

@skip("use a different way to specify filter other than class variable..")
def test_filter():
    import wereyouhere.generator.custom as custom_gen
    from wereyouhere.generator.plaintext import extract_from_path

    History.add_filter(r'some-weird-domain')
    hist = custom_gen.get_custom_history(
        extract_from_path('testdata/custom'),
    )
    assert len(hist) == 4 # chrome-error got filtered out

def test_custom():
    import wereyouhere.generator.custom as custom_gen

    hist = custom_gen.get_custom_history(
        """grep -Eo -r --no-filename '(http|https)://\S+' testdata/custom""",
        tag='test',
    )
    assert len(hist) == 5 # TODO this will be changed later when we actually normalise
    with TemporaryDirectory() as tdir:
        render([hist], join(tdir, 'res.json'))

def merge(merged: str, chunk: str):
    from subprocess import check_call
    # TODO assert that argument orders is correct (e.g. check original db schema)
    # TODO script relative to path
    check_call(['/L/coding/were-you-here/scripts/merge-chrome-db/merge.sh', merged, chunk])

def test_merge():
    testdata_path = "/L/data/wereyouhere/chrome-history"
    first  = join(testdata_path, "20180415/History")
    second = join(testdata_path, "20180417/History")
    with TemporaryDirectory() as tdir:
        merged_path = join(tdir, 'merged.sql')

        def merged_size() -> int:
            return getsize(merged_path)

        merge(merged_path, first)
        fsize = merged_size()

        merge(merged_path, first)
        fsize_2 = merged_size()

        assert fsize == fsize_2

        merge(merged_path, second)
        ssize = merged_size()

        assert ssize > fsize

        merge(merged_path, second)
        ssize_2 = merged_size()

        assert ssize_2 == ssize

