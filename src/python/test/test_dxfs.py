#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 DNAnexus, Inc.
#
# This file is part of dx-toolkit (DNAnexus platform client libraries).
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may not
#   use this file except in compliance with the License. You may obtain a copy
#   of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import os, sys, unittest, json, tempfile, subprocess, csv, shutil, re, time

from dxpy_testutil import DXTestCase

import dxpy

class TestDXFS(DXTestCase):
    @unittest.skipIf('DXTEST_FUSE' not in os.environ,
                     'skipping test that would mount FUSE filesystems')
    def test_dxfs_operations(self):
        project_handle = dxpy.DXProject(self.project)
        subprocess.check_call(['dx', 'mkdir', 'foo'])
        subprocess.check_call(['dx', 'mkdir', 'bar'])
        #subprocess.check_call(['dx', 'mkdir', '-p', '/bar/baz'])
        dxpy.upload_local_file(__file__, wait_on_close=True)
        
        mountpoint = tempfile.mkdtemp()
        fuse_driver = subprocess.Popen(['dx-mount', mountpoint])
        self.assertEqual(fuse_driver.poll(), None)
        time.sleep(1)
        self.assertEqual(set(os.listdir(mountpoint)), set(['foo', 'bar', os.path.basename(__file__)]))
        
        # Reading
        self.assertEqual(open(__file__).read(), open(os.path.join(mountpoint, __file__)).read())
        
        # Moving
        shutil.move(os.path.join(mountpoint, __file__), os.path.join(mountpoint, __file__+"2"))
        self.assertEqual(set(os.listdir(mountpoint)), set(['foo', 'bar', os.path.basename(__file__+"2")]))
        shutil.move(os.path.join(mountpoint, __file__+"2"), os.path.join(mountpoint, "foo"))
        self.assertEqual(set(os.listdir(os.path.join(mountpoint, 'foo'))), set([os.path.basename(__file__+"2")]))
        folder_listing = project_handle.list_folder('/foo')
        self.assertEqual(len(folder_listing['folders']), 0)
        self.assertEqual(len(folder_listing['objects']), 1)
        self.assertEqual(dxpy.get_handler(folder_listing['objects'][0]['id']).name, os.path.basename(__file__+"2"))
        self.assertEqual(open(__file__).read(), open(os.path.join(mountpoint, 'foo', __file__+"2")).read())
        
        # Making directories
        os.mkdir(os.path.join(mountpoint, 'xyz'))
        self.assertIn('/xyz', project_handle.list_folder('/')['folders'])
        os.mkdir(os.path.join(mountpoint, 'xyz', 'abc'))
        self.assertIn('/xyz/abc', project_handle.list_folder('/xyz')['folders'])
        os.rmdir(os.path.join(mountpoint, 'xyz', 'abc'))
        self.assertNotIn('/xyz/abc', project_handle.list_folder('/xyz')['folders'])
        os.rmdir(os.path.join(mountpoint, 'xyz'))
        self.assertNotIn('/xyz', project_handle.list_folder('/')['folders'])
        
        fuse_driver.terminate()

if __name__ == '__main__':
    unittest.main()
