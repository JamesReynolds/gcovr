import glob
import os
import os.path
import platform
import pytest
import re
import subprocess
import sys

from pyutilib.misc.pyyaml_util import compare_repn as compare_xml
from pyutilib.misc.xmltodict import parse as parse_xml


python_interpreter = sys.executable.replace('\\', '/')  # use forward slash on windows as well
env = os.environ
env['GCOVR'] = python_interpreter + ' -m gcovr'
if sys.version_info < (2, 7):  # pragma: no cover
    # fallback for "python -m module"
    env['GCOVR'] = 'gcovr'

basedir = os.path.split(os.path.abspath(__file__))[0]

RE_DECIMAL = re.compile(r'(\d+\.\d+)')

RE_TXT_WHITESPACE = re.compile(r'[ ]+$', flags=re.MULTILINE)

RE_XML_ATTRS = re.compile(r'(timestamp)="[^"]*"')
RE_XML_GCOVR_VERSION = re.compile(r'version="gcovr [^"]+"')

RE_HTML_ATTRS = re.compile('((timestamp)|(version))="[^"]*"')
RE_HTML_FOOTER_VERSION = re.compile(
    '(Generated by: <a [^>]+>GCOVR \\(Version) 3.[\w.-]+(\\)</a>)')
RE_HTML_HEADER_DATE = re.compile(
    '(<td class="headerValue")>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d<(/td>)')


def scrub_txt(contents):
    return RE_TXT_WHITESPACE.sub('', contents)


def scrub_xml(contents):
    contents = RE_DECIMAL.sub(lambda m: str(round(float(m.group(1)), 5)), contents)
    contents = RE_XML_ATTRS.sub(r'\1=""', contents)
    contents = RE_XML_GCOVR_VERSION.sub('version=""', contents)
    contents = contents.replace("\r", "")
    return contents


def scrub_html(contents):
    contents = RE_HTML_ATTRS.sub('\\1=""', contents)
    contents = RE_HTML_FOOTER_VERSION.sub("\\1 3.x\\2", contents)
    contents = RE_HTML_HEADER_DATE.sub("\\1>0000-00-00 00:00:00<\\2", contents)
    contents = contents.replace("\r", "")
    return contents


def findtests(basedir):
    for f in os.listdir(basedir):
        if not os.path.isdir(os.path.join(basedir, f)):
            continue
        if f.startswith('.'):
            continue
        if 'pycache' in f:
            continue
        yield f


def assert_xml_equals(coverage, reference):
    coverage_repn = parse_xml(coverage)
    reference_repn = parse_xml(reference)
    compare_xml(reference_repn, coverage_repn, tolerance=1e-4, exact=True)


def run(cmd):
    print("STDOUT - START", str(cmd))
    returncode = subprocess.call(cmd, stderr=subprocess.STDOUT, env=env)
    print("STDOUT - END")
    return returncode == 0


def find_reference_files(pattern):
    for reference in glob.glob("reference/" + pattern):
        coverage = os.path.basename(reference)
        yield coverage, reference


SCRUBBERS = dict(
    txt=scrub_txt,
    xml=scrub_xml,
    html=scrub_html)

OUTPUT_PATTERN = dict(
    txt='coverage.txt',
    xml='coverage.xml',
    html='coverage*.html')

ASSERT_EQUALS = dict(
    xml=assert_xml_equals)


@pytest.mark.parametrize('name', findtests(basedir))
@pytest.mark.parametrize('format', ['txt', 'xml', 'html'])
def test_build(name, format):
    scrub = SCRUBBERS[format]
    output_pattern = OUTPUT_PATTERN[format]
    assert_equals = ASSERT_EQUALS.get(format, None)

    is_windows = platform.system() == 'Windows'
    if name == 'linked' and format == 'html' and is_windows:
        pytest.xfail("have yet to figure out symlinks on Windows")

    os.chdir(os.path.join(basedir, name))
    assert run(["make", "clean"])
    assert run(["make"])
    assert run(["make", format])

    for coverage_file, reference_file in find_reference_files(output_pattern):
        with open(coverage_file) as f:
            coverage = scrub(f.read())
        with open(reference_file) as f:
            reference = scrub(f.read())

        if assert_equals is not None:
            assert_equals(coverage, reference)
        else:
            assert coverage == reference, "coverage={0}, reference={1}".format(
                coverage_file, reference_file)

    assert run(["make", "clean"])
    os.chdir(basedir)
