#!/usr/bin/env python
import os
import os.path
import re
import sys
import subprocess
import traceback
import pyutilib.th as unittest

basedir = os.path.split(os.path.abspath(__file__))[0]
starting_dir = os.getcwd()


@unittest.category('smoke')
class GcovrTxt(unittest.TestCase):
    def __init__(self, *args, **kwds):
        unittest.TestCase.__init__(self, *args, **kwds)


@unittest.category('smoke')
class GcovrXml(unittest.TestCase):
    def __init__(self, *args, **kwds):
        unittest.TestCase.__init__(self, *args, **kwds)
        self.xml_attrs_re = re.compile(r'(timestamp)="[^"]*"')
        self.gcovr_version_re = re.compile(r'version="gcovr [^"]+"')

    def scrub_xml(self, filename):
        F = open(filename)
        contents = F.read()
        F.close()

        contents = self.xml_attrs_re.sub('\\1=""', contents)
        contents = self.gcovr_version_re.sub('version=""', contents)
        contents = contents.replace("\r", "")

        F = open(filename, 'w')
        F.write(contents)
        F.close()

    def compare_xml(self):
        coverage = 'coverage.xml'
        reference = os.path.join('reference', 'coverage.xml')
        self.scrub_xml(coverage)
        self.scrub_xml(reference)
        self.assertMatchesXmlBaseline(coverage, reference, tolerance=1e-4, exact=True)


@unittest.category('smoke')
class GcovrHtml(unittest.TestCase):
    def __init__(self, *args, **kwds):
        unittest.TestCase.__init__(self, *args, **kwds)
        self.xml_re = re.compile('((timestamp)|(version))="[^"]*"')
        self.footer_version_re = re.compile(
            '(Generated by: <a [^>]+>GCOVR \\(Version) 3.[\w.-]+(\\)</a>)')
        self.header_date_re = re.compile(
            '(<td class="headerValue")>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d<(/td>)')

    def scrub_html(self, filename):
        F = open(filename)
        scrubbedData = F.read()
        scrubbedData = self.xml_re.sub('\\1=""', scrubbedData)
        scrubbedData = self.footer_version_re.sub("\\1 3.x\\2", scrubbedData)
        scrubbedData = self.header_date_re.sub("\\1>0000-00-00 00:00:00<\\2", scrubbedData)
        scrubbedData = scrubbedData.replace("\r", "")
        F.close()

        F = open(filename, 'w')
        F.write(scrubbedData)
        F.close()

    def compare_html(self):
        self.scrub_html("coverage.html")
        self.scrub_html("reference/coverage.html")
        # Can't use assertMatchesXmlBaseline()
        # because HTML doesn't parse as valid XML.
        # The pyutilib does not seem to contain HTML comparison functions.
        self.assertFileEqualsBaseline('coverage.html', os.path.join('reference', 'coverage.html'), tolerance=1e-4)


def run(cmd):
    try:
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                env=os.environ)
        print("STDOUT - START")
        sys.stdout.write("%s" % proc.communicate()[0])
        print("STDOUT - END")
        return not proc.returncode
    except Exception:
        e = sys.exc_info()[1]
        sys.stdout.write("Caught unexpected exception in test driver: %s\n%s"
                         % (str(e), traceback.format_exc()))
        raise


@unittest.nottest
def gcovr_test_txt(self, name):
    os.chdir(os.path.join(basedir, name))
    run(["make", "clean"]) or self.fail("Clean failed")
    run(["make"]) or self.fail("Make failed")
    run(["make", "txt"]) or self.fail("Execution failed")
    self.assertFileEqualsBaseline("coverage.txt", "reference/coverage.txt")
    run(["make", "clean"]) or self.fail("Clean failed")
    os.chdir(basedir)


@unittest.nottest
def gcovr_test_xml(self, name):
    os.chdir(os.path.join(basedir, name))
    run(["make", "clean"]) or self.fail("Clean failed")
    run(["make"]) or self.fail("Make failed")
    run(["make", "xml"]) or self.fail("Execution failed")
    self.compare_xml()
    run(["make", "clean"]) or self.fail("Clean failed")
    os.chdir(basedir)


@unittest.nottest
def gcovr_test_html(self, name):
    os.chdir(os.path.join(basedir, name))
    run(["make"]) or self.fail("Make failed")
    run(["make", "html"]) or self.fail("Execution failed")
    self.compare_html()
    run(["make", "clean"]) or self.fail("Clean failed")
    os.chdir(basedir)


skip_dirs = ['.', '..', '.svn']

for f in os.listdir(basedir):
    if os.path.isdir(os.path.join(basedir, f)) and f not in skip_dirs:
        if 'pycache' in f:
            continue
        GcovrTxt.add_fn_test(fn=gcovr_test_txt, name=f)
        GcovrXml.add_fn_test(fn=gcovr_test_xml, name=f)
        GcovrHtml.add_fn_test(fn=gcovr_test_html, name=f)

if __name__ == "__main__":
    unittest.main()
