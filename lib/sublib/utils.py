# -*- coding: utf-8 -*-
'''
    Author    : Huseyin BIYIK <husenbiyik at hotmail>
    Year      : 2016
    License   : GPL

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import xbmcvfs
import xbmcgui
import xbmc

import re
import urllib
import urllib2
import urlparse
import cookielib
import unicodedata
import HTMLParser
import os

_cj = cookielib.CookieJar()
_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(_cj))
_hparser = HTMLParser.HTMLParser()

_ua = "KODI / XBMC Sublib Library"

epiregs = [
            r"s([0-9]+)xe([0-9]+)",
            r"s([0-9]+)x([0-9]+)",
            r"s([0-9]+)e([0-9]+)",
            r"s([0-9]+)-e([0-9]+)",
            r"s([0-9]+)_e([0-9]+)",
            r"s([0-9]+) e([0-9]+)",
            r"([0-9]+)x([0-9]+)",
            r"([0-9]+)-([0-9]+)",
            r"([0-9]+)_([0-9]+)",
            r"-([0-9]+)",
            r"_([0-9]+)",
            ]


def normstr(s):
    s = unicodedata.normalize('NFKD', unicode(unicode(s, 'utf-8')))
    return s.encode('ascii', 'ignore')


def dformat(d, m):
    r = {}
    for k, v in d.iteritems():
        try:
            r[k] = m(v)
        except:
            r[k] = v
    return r


def download(u, query=None, data=None, referer=None, binary=False, ua=None,
             encoding="utf-8"):
    if not ua:
        ua = _ua
    if query:
        q = urllib.urlencode(query)
        u += "?" + q
    if data:
        data = urllib.urlencode(data)
    header = {"User-Agent": ua}
    if referer:
        header["Referer"] = referer
    # print u
    req = urllib2.Request(u, data, header)
    res = _opener.open(req)
    if not binary:
        res = res.read()
        res = res.decode(encoding)
        res = _hparser.unescape(res)
    return res


def checkarchive(fname):
    with open(fname) as f:
        sign = f.read(4)
    if sign == "Rar!":
        return "rar"
    elif sign == "\x50\x4B\x03\x04":
        return "zip"


def selectfile(files, prefix="/"):
    if not len(files):
        return
    optlist = []
    dirindex = []
    optindex = -1
    if not prefix == "/":
        optlist.append("..")
        optindex += 1
    for f in files:
        if f.endswith("/"):
            fpath, fname = os.path.split(f[:-1])
            fname = None
        else:
            fpath, fname = os.path.split(f)
        if not fpath == "/":
            fpath += "/"
        if fpath == prefix:
            if fname:
                optlist.append(fname)
                optindex += 1
            else:
                optlist.append("[%s]" % f.split("/")[-2])
                optindex += 1
                dirindex.append(optindex)
    dialog = xbmcgui.Dialog()
    index = dialog.select(xbmc.getLocalizedString(13250), optlist)
    if index < 0:
        # canceled
        return
    if index == 0 and not prefix == "/":
        # parent directory
        prefix = "/".join(prefix.split("/")[:-2]) + "/"
        return selectfile(files, prefix)
    if index in dirindex:
        # sub-folder
        prefix += optlist[index][1:-1] + "/"
        ret = selectfile(files, prefix)
        if ret < 0:
            nprefix = os.path.split(prefix[:-1])[0] + "/"
            nprefix = nprefix.replace("//", "/")
            return selectfile(files, nprefix)
        else:
            return ret
    else:
        # single file
        return prefix + optlist[index]


def getlof(ar, fname, path="", lof=[]):
    ds, fs = xbmcvfs.listdir("%s://%s%s" % (ar, urllib.quote_plus(fname),
                                            path))
    for d in ds:
        dpath = path + "/" + d
        lof.append(dpath + "/")
        getlof(ar, fname, dpath, lof)
    for f in fs:
        lof.append(path + "/" + f)
    return lof


def findshow(season, episode, fname):
    matchstr = os.path.split(fname)[1]
    matchstr = matchstr.lower().replace(" ", "")
    if not episode == -1:
        for reg in epiregs:
            m = re.search(reg, matchstr)
            if m and m.lastindex == 2 and\
                    m.group(1).isdigit() and \
                    m.group(2).isdigit() and \
                    int(m.group(1)) == season and \
                    int(m.group(2)) == episode:
                # print "!!!!!!matched %s:%s" % (matchstr, reg)
                return fname
            if m and m.lastindex == 1 and\
                    m.group(1).isdigit() and \
                    int(m.group(1)) == episode and \
                    season < 0:
                # print "++++++matched %s:%s" % (matchstr, reg)
                return fname


def getar(fname, ar, show, season, episode):
    if fname.endswith("/"):
        fname = fname[:-1]
    lof = getlof(ar, fname)
    if show:
        found = []
        for f in lof:
            if f.endswith("/"):
                continue
            fname = findshow(season, episode, f)
            if fname:
                found.append(fname)
        if len(found):
            lof = found
    if len(lof) == 1:
        return lof[0]
    else:
        return selectfile(lof)


def getsub(fname, show, season, episode):
    isar = checkarchive(fname)
    if isar:
        arname = getar(fname, isar, show, season, episode)
        if not arname:
            return
        uri = "%s://%s%s" % (isar, urllib.quote_plus(fname), arname)
        # fix for rar file system crashes sometimes if archive:// is returned
        fname = fname + arname.replace("/", "_")
        f = xbmcvfs.File(uri)
        with open(fname, "w") as out:
            out.write(f.read())
        f.close()
        return fname
    else:
        return fname


def infofrompath(path, item):
    path = urlparse.urlparse(str(path)).path
    path = urllib.unquote_plus(path)
    if path.endswith("/"):
        path = path[:-1]
    fname = os.path.split(path)[1]
    regmatch = False
    for reg in epiregs:
        reg = "(.*)" + reg
        matchstr = fname.lower().replace(".", " ")
        matchstr = matchstr.replace(",", " ")
        matchstr = matchstr.replace("_", " ")
        matchstr = matchstr.replace("-", " ")
        m = re.search(reg, matchstr)
        if m and m.lastindex == 3:
            regmatch = True
            # epi,sea
            item.show = True
            item.title = m.group(1)
            if m.group(2).isdigit():
                item.season = int(m.group(2))
            if m.group(3).isdigit():
                item.episode = int(m.group(3))
        if m and m.lastindex == 2:
            regmatch = True
            # epi only
            item.show = True
            item.title = m.group(1)
            if m.group(2).isdigit():
                item.season = -1
                item.episode = int(m.group(2))
        if regmatch:
            break
    if not regmatch:
        # remove extension
        if "." in fname:
            fname = ".".join(fname.split(".")[:-1])
        item.title = fname
    return item
