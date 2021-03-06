#!/usr/bin/python
# -*- encoding: utf-8 -*-
# *
# *  Copyright (C) 2012-2013 Garrett Brown
# *  Copyright (C) 2010      j48antialias
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# *  Based on code by j48antialias:
# *  https://anarchintosh-projects.googlecode.com/files/addons_xml_generator.py
# *  Modified (Globals, Zip-Part) by b-jesch

""" addons.xml generator """

import os
import sys
import zipfile
import shutil
import hashlib
from xml.dom import minidom

'''
#############################################
####                                     ####
#### START OF THE USER MODIFICATION AREA ####
####                                     ####
#############################################
'''

'''
This is a list of your addons within the addon directory of your running kodi installation. These are also
your addons which should deployed to your repository on github. Modify the list to your needs. At least the
repository itself should be included in this list.
'''

# 'script.service.caretaker',  temporary removed

MY_ADDONS = ['plugin.video.ipcams', 'repository.saxbmc', 'script.helper.bumblebox', 'script.homematic.sonoff',
             'script.loungeripper', 'script.module.oauth2client', 'script.program.driverselect', 'script.input.adsp',
             'script.program.fritzact', 'script.service.gto', 'script.video.binge', 'script.service.hypercon',
             'service.calendar', 'service.fritzbox.callmonitor', 'service.kn.switchtimer', 'service.lgtv.remote',
             'service.librespot', 'service.pvr.manager', 'service.sleepy.watchdog',
             ]

'''
Files/folders that should exclude from repository file system.
'''

EXCLUDES = ['.git', '.idea', '.gitattributes']

'''
The base directory of your running kodi installation. You could use relative or absolute paths depending on
your installation. This script must have access to the base folder. Also check the access permissions of the
content. 
'''

BASEDIR = '../addons'

'''
The working directory where the addon.xml and the checksum file (md5) of your repository resides 
'''

WORKINGDIR = os.getcwd()

'''
The directory of the zipped repository addons. This folder resides within the repository normally. If you start
with a fresh installation of your repo, clear the content of this folder.
'''

ZIPDIR = 'zip'

'''
The extension of your zipped addon. This should'nt be changed.
'''
ZIPEXT = '.zip'

'''
###########################################
####                                   ####
#### END OF THE USER MODIFICATION AREA ####
####                                   ####
###########################################
'''

# Compatibility with 3.0, 3.1 and 3.2 not supporting u"" literals
if sys.version < '3':
    import codecs

    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x


class Generator:
    """
        Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file. Must be run from the root of
        the checked-out repo. Only handles single depth folder structure.
        Additional creates versioned zipfiles in a zipfolder from a project
        structure.
    """

    def __init__(self):
        # generate files
        self._create_zipfiles()
        self._generate_addons_file()
        self._generate_md5_file()
        # notify user
        print("Finished creating zipfiles, updating addons.xml and md5 files")


    def _create_zipfiles(self):
        os.chdir(BASEDIR)
        addons = os.listdir('.')

        for addon in addons:
            if addon in MY_ADDONS:
                try:
                    _dir = os.path.join(WORKINGDIR, ZIPDIR, addon)
                    if not os.path.exists(_dir): os.makedirs(_dir)
                    _file = os.path.join(_dir, addon)
                    addon_zip = zipfile.ZipFile(_file, 'w')
                    for addon_root, dirs, files in os.walk(addon):
                        addon_icon_found = False
                        fanart_bg_found = False
                        dirs[:] = [d for d in dirs if d not in EXCLUDES]
                        for filename in files:
                            if os.path.basename(filename)[0:1] == '.' or os.path.basename(filename)[-3:] == 'pyo' \
                                    or os.path.basename(filename)[-3:] == 'pyc':
                                continue
                            if os.path.basename(filename) == 'changelog.txt':
                                shutil.copyfile(os.path.join(addon_root, filename), os.path.join(_dir, 'changelog.txt'))
                            if os.path.basename(filename) == 'icon.png' and not addon_icon_found:
                                shutil.copyfile(os.path.join(addon_root, filename), os.path.join(_dir, 'icon.png'))
                                addon_icon_found = True
                            if os.path.basename(filename) == 'fanart.jpg' and not fanart_bg_found:
                                shutil.copyfile(os.path.join(addon_root, filename), os.path.join(_dir, 'fanart.jpg'))
                                fanart_bg_found = True
                            if os.path.basename(filename) == 'addon.xml':
                                # parse this
                                _xmldoc = minidom.parse(os.path.join(addon_root, filename))
                                _vers = _xmldoc.getElementsByTagName('addon')
                                for _attr in  _vers: _v = _attr.getAttribute('version')
                                print _file, _v

                            addon_zip.write(os.path.join(addon_root, filename), compress_type=zipfile.ZIP_DEFLATED)
                    addon_zip.close()
                    _final = _file + '-' + _v + ZIPEXT
                    if os.path.exists(_final): os.remove(_final)
                    os.rename(_file, _final)

                except Exception as e:
                    # oops
                    print("An error occurred while creating %s file!\n%s" % (_file, e))

    def _generate_addons_file(self):
        os.chdir(BASEDIR)
        addons = os.listdir('.')
        # final addons text
        addons_xml = u("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<addons>\n")
        # loop thru and add each addons addon.xml file
        for addon in addons:
            if addon in MY_ADDONS:
                try:
                    # skip any file or .svn folder or .git folder
                    if ( not os.path.isdir(addon) or addon == ".svn" or addon == ".git" ): continue
                    _path = os.path.join(addon, "addon.xml")
                    xml_lines = open(_path, "r").read().splitlines()

                    addon_xml = ""
                    for line in xml_lines:
                        # skip encoding format line
                        if (line.find("<?xml") >= 0): continue
                        # add line
                        if sys.version < '3':
                            addon_xml += '\t' + unicode(line.rstrip() + "\n", "UTF-8")
                        else:
                            addon_xml += '\t' + line.rstrip() + "\n"
                    # we succeeded so add to our final addons.xml text
                    addons_xml += addon_xml.rstrip() + "\n\n"
                except Exception, e:
                    # missing or poorly formatted addon.xml
                    print("Excluding %s due reason: %s" % ( _path, e ))

        addons_xml = addons_xml.strip() + u("\n</addons>\n")
        self._save_file(addons_xml.encode("UTF-8"), file="addons.xml")

    def _generate_md5_file(self):
        # create a new md5 hash
        os.chdir(WORKINGDIR)
        try:
            m = hashlib.md5(open("addons.xml", "r").read().encode("UTF-8")).hexdigest()
        except UnicodeDecodeError:
            m = hashlib.md5(open("addons.xml", "r").read()).hexdigest()

        # save file
        try:
            self._save_file(m.encode("UTF-8"), file="addons.xml.md5")
        except Exception as e:
            # oops
            print("An error occurred creating addons.xml.md5 file!\n%s" % e)

    def _save_file(self, data, file):
        try:
            # write data to the file (use b for Python 3)
            open(os.path.join(WORKINGDIR, file), "wb").write(data)
        except Exception as e:
            # oops
            print("An error occurred saving %s file!\n%s" % (file, e))


if (__name__ == "__main__"):
    # start
    Generator()
