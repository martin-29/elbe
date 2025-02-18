# ELBE - Debian Based Embedded Rootfilesystem Builder
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2013-2018 Linutronix GmbH

import os
import re
import subprocess

import apt.debfile

from elbepack.filesystem import TmpdirFilesystem


class NoPackageException(Exception):
    pass


def get_sources_list(prj):

    suite = prj.text('suite')

    slist = ''
    if prj.has('mirror/primary_host'):
        protocl = f"{prj.text('mirror/primary_proto')}"
        host = f"{prj.text('mirror/primary_host').replace('LOCALMACHINE', '10.0.2.2')}"
        path = f"{prj.text('mirror/primary_path')}"
        mirror = f'{protocl}://{host}/{path}'
        slist += f'deb {mirror} {suite} main\n'
        slist += f'deb-src {mirror} {suite} main\n'

    if prj.node('mirror/url-list'):
        for n in prj.node('mirror/url-list'):
            if n.has('binary'):
                tmp = n.text('binary').replace('LOCALMACHINE', '10.0.2.2')
                slist += f'deb {tmp.strip()}\n'
            if n.has('source'):
                tmp = n.text('source').replace('LOCALMACHINE', '10.0.2.2')
                slist += f'deb-src {tmp.strip()}\n'

    return slist


def get_key_list(prj):
    retval = []
    if prj.node('mirror/url-list'):
        for n in prj.node('mirror/url-list'):
            if n.has('key'):
                tmp = n.text('key').replace('LOCALMACHINE', '10.0.2.2')
                retval.append(tmp.strip())

    return retval


def get_dsc_size(fname):
    sz = os.path.getsize(fname)

    dsc = apt.debfile.DscSrcPackage(fname)
    filesizes = map(int, dsc._sections['Files'].split()[1::3])
    sz += sum(filesizes)

    return sz


class ChangelogNeedsDependency(Exception):
    def __init__(self, pkgname):
        super().__init__(f'Changelog extraction depends on "{pkgname}"')
        self.pkgname = pkgname


re_pkgfilename = r'(?P<name>.*)_(?P<ver>.*)_(?P<arch>.*).deb'


def extract_pkg_changelog(fname, extra_pkg=None):
    pkgname = os.path.basename(fname)
    m = re.match(re_pkgfilename, pkgname)

    pkgname = m.group('name')
    pkgarch = m.group('arch')

    print(f'pkg: {pkgname}, arch: {pkgarch}')

    fs = TmpdirFilesystem()

    if extra_pkg:
        print('with extra ' + extra_pkg)
        subprocess.run(['dpkg', '-x', extra_pkg, fs.fname('/')], check=True)

    subprocess.run(['dpkg', '-x', fname, fs.fname('/')], check=True)

    dch_dir = f'/usr/share/doc/{pkgname}'

    if fs.islink(dch_dir) and not extra_pkg:
        lic = fs.readlink(dch_dir)
        print(dch_dir, lic)
        raise ChangelogNeedsDependency(lic)

    dch_bin = f'/usr/share/doc/{pkgname}/changelog.Debian.{pkgarch}.gz'
    dch_src = f'/usr/share/doc/{pkgname}/changelog.Debian.gz'

    ret = ''

    if fs.exists(dch_bin):
        ret += fs.read_file(dch_bin, gz=True).decode(encoding='utf-8',
                                                     errors='replace')

    if fs.exists(dch_src):
        ret += fs.read_file(dch_src, gz=True).decode(encoding='utf-8',
                                                     errors='replace')

    return ret
