# ELBE - Debian Based Embedded Rootfilesystem Builder
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2014-2017 Linutronix GmbH

import importlib.resources
import os

from mako import exceptions
from mako.template import Template

import elbepack
import elbepack.makofiles
from elbepack.treeutils import etree


def fix_linebreak_escapes(s):
    return s.replace('\\\n', '${"\\\\"}\n')


def template(fname, d, linebreak=False):
    try:
        return Template(
            filename=os.fspath(fname),
            preprocessor=fix_linebreak_escapes if linebreak else None,
        ).render(**d)
    except BaseException:
        print(exceptions.text_error_template().render())
        raise


def write_template(outname, fname, d, linebreak=False):
    outfile = open(outname, 'w')
    outfile.write(template(fname, d, linebreak))
    outfile.close()


def write_pack_template(outname, fname, d, linebreak=False):
    template_dir = importlib.resources.files(elbepack.makofiles)

    with importlib.resources.as_file(template_dir / fname) as template:
        write_template(outname, template, d, linebreak)


def _default_preseed():
    with importlib.resources.files(elbepack) / 'default-preseed.xml' as f:
        return etree(f)


def get_preseed(xml):
    def_xml = _default_preseed()

    preseed = {}
    for c in def_xml.node('/preseed'):
        k = (c.et.attrib['owner'], c.et.attrib['key'])
        v = (c.et.attrib['type'], c.et.attrib['value'])

        preseed[k] = v

    if not xml.has('./project/preseed'):
        return preseed

    for c in xml.node('/project/preseed'):
        k = (c.et.attrib['owner'], c.et.attrib['key'])
        v = (c.et.attrib['type'], c.et.attrib['value'])

        preseed[k] = v

    return preseed


def get_initvm_preseed(xml):
    def_xml = _default_preseed()

    preseed = {}
    for c in def_xml.node('/preseed'):
        k = (c.et.attrib['owner'], c.et.attrib['key'])
        v = (c.et.attrib['type'], c.et.attrib['value'])

        preseed[k] = v

    if not xml.has('./initvm/preseed'):
        return preseed

    for c in xml.node('/initvm/preseed'):
        k = (c.et.attrib['owner'], c.et.attrib['key'])
        v = (c.et.attrib['type'], c.et.attrib['value'])

        preseed[k] = v

    return preseed


def preseed_to_text(pres):
    retval = ''
    for k, v in pres.items():
        retval += f'{k[0]}\t{k[1]}\t{v[0]}\t{v[1]}\n'

    return retval
