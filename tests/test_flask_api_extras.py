# -*- coding: utf-8 -*-
#
# Copyright © 2013  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

'''
pkgdb tests for the Flask API regarding collections.
'''

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import json
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import pkgdb
from pkgdb.lib import model
from tests import (Modeltests, FakeFasUser, create_package_acl)


class FlaskApiExtrasTest(Modeltests):
    """ Flask API extras tests. """

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApiExtrasTest, self).setUp()

        pkgdb.APP.config['TESTING'] = True
        pkgdb.SESSION = self.session
        pkgdb.api.acls.SESSION = self.session
        self.app = pkgdb.APP.test_client()
        # Let's make sure the cache is empty for the tests
        pkgdb.cache.invalidate()

    def test_api_bugzilla(self):
        """ Test the api_bugzilla function.  """

        pkgdb.cache.invalidate()
        output = self.app.get('/api/bugzilla/')
        self.assertEqual(output.status_code, 200)

        expected = """# Package Database VCS Acls
# Text Format
# Collection|Package|Description|Owner|Initial QA|Initial CCList
# Backslashes (\) are escaped as \u005c Pipes (|) are escaped as \u007c

Fedora|geany|IDE|toshio|pingou
Fedora|guake|Drop down terminal|pingou|spot
Fedora|python-gpgme|GPG module in python|toshio|
Fedora|perl-foo|Foor in perl|group::perl-sig|
Fedora|perl-bar|Bar in perl|group::perl-sig|
Fedora|test|test|pingou|test
Fedora|test2|test|test|"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/bugzilla/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)
        expected = {u'bugzillaAcls': {u'Fedora': [
            {u'geany':
                {u'owner': u'toshio', u'cclist':
                    {u'groups': [], u'people': [u'pingou']},
                 u'qacontact': None,
                 u'summary': u'IDE'}},
            {u'guake':
                {u'owner': u'pingou', u'cclist':
                    {u'groups': [], u'people': [u'spot']},
                 u'qacontact': None,
                 u'summary': u'Drop down terminal'}},
            {u'python-gpgme':
                {u'owner': u'toshio', u'cclist':
                    {u'groups': [], u'people': []},
                 u'qacontact': None,
                 u'summary': u'GPG module in python'}},
            {u'perl-foo':
                {u'owner': u'group::perl-sig', u'cclist':
                    {u'groups': [], u'people': []},
                 u'qacontact': None,
                 u'summary': u'Foor in perl'}},
            {u'perl-bar':
                {u'owner': u'group::perl-sig', u'cclist':
                    {u'groups': [], u'people': []},
                 u'qacontact': None,
                 u'summary': u'Bar in perl'}},
            {u'test':
                {u'owner': u'pingou', u'cclist':
                    {u'groups': [], u'people': [u'test']},
                 u'qacontact': None,
                 u'summary': u'test'}},
            {u'test2':
                {u'owner': u'test', u'cclist':
                    {u'groups': [], u'people': []},
                 u'qacontact': None,
                 u'summary': u'test'}}
        ]}, u'title': u'Fedora Package Database -- Bugzilla ACLs'}

        self.assertEqual(data, expected)

    def test_api_notify(self):
        """ Test the api_notify function.  """

        output = self.app.get('/api/notify/')
        self.assertEqual(output.status_code, 200)

        expected = """geany|toshio,pingou
guake|pingou,spot
python-gpgme|toshio
perl-foo|group::perl-sig
perl-bar|group::perl-sig
test|test,pingou
test2|test,pingou"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/notify/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'title': u'Fedora Package Database -- Notification List',
            u'packages': [
                {u'geany': [u'toshio', u'pingou']},
                {u'guake': [u'pingou', u'spot']},
                {u'python-gpgme': [u'toshio']},
                {u'perl-foo': [u'group::perl-sig']},
                {u'perl-bar': [u'group::perl-sig']},
                {u'test': [u'test', u'pingou']},
                {u'test2': [u'test', u'pingou']}
            ], u'name': None, u'version': None, u'eol': False
        }
        self.assertEqual(data, expected)

    def test_api_vcs(self):
        """ Test the api_vcs function.  """

        output = self.app.get('/api/vcs/')
        self.assertEqual(output.status_code, 200)

        expected = """# VCS ACLs
# avail|@groups,users|rpms/Package/branch

avail | @provenpackager,toshio,pingou | rpms/geany/master
avail | @provenpackager,toshio,pingou | rpms/geany/f19
avail | @provenpackager,pingou,spot | rpms/guake/master
avail | @provenpackager,pingou | rpms/guake/f19
avail | @provenpackager,toshio | rpms/python-gpgme/master
avail | @provenpackager,toshio | rpms/python-gpgme/f19
avail | @provenpackager,@perl-sig, | rpms/perl-foo/master
avail | @provenpackager,@perl-sig, | rpms/perl-foo/f19
avail | @provenpackager,@perl-sig, | rpms/perl-bar/master
avail | @provenpackager,test,pingou | rpms/test/master
avail | @provenpackager,test | rpms/test/f19
avail | @provenpackager,test,pingou | rpms/test2/master
avail | @provenpackager,test | rpms/test2/f19"""
        self.assertEqual(output.data, expected)

        output = self.app.get('/api/vcs/?format=json')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.data)

        expected = {
            u'packageAcls': {
                u'f19': {
                    u'commit': {
                        u'groups': [u'provenpackager'],
                        u'people': [u'test']
                    }
                },
                u'master': {
                    u'commit': {
                        u'groups': [u'provenpackager'],
                        u'people': [u'test', u'pingou']
                    }
                }
            },
            u'title': u'Fedora Package Database -- VCS ACLs'}
        self.assertEqual(data, expected)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApiExtrasTest)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
