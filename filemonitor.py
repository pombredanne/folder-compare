import sys, os
import time
import filecmp
import hashlib
import ast
import logging
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
)
# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

hdlr = logging.FileHandler('info.log')
format = '%(asctime)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s',
format = '%(asctime)s %(levelname)s %(message)s'
formatter = logging.Formatter(format)
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 


SNAPSHOT = "\\files.snapshot"
CHANGELOG = "change_list.log"
class FolderNotExistsException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class FileMeta(object):
    """
    FileMeta - build up the file snapshot by sha-1.
    """
    def __init__(self, full, base, file, size):
        self.full = full + '\\' + file
        self.base = base
        self.file = file
        self.relative_path = base + '\\' + file
        self.size = size
        self.reason = ''
        self.hash = self._hash()

    def _hash(self):
        filepath = self.full
        sha1 = hashlib.sha1()
        f = open(filepath, 'rb')
        try:
            sha1.update(f.read())
        finally:
            f.close()
        logger.debug("%s - %s" % (sha1.hexdigest(), filepath))
        return sha1.hexdigest()

class DiffScanner(object):
    """
    compare 2 version folder, look up difference. 
    """
    def __init__(self, new_version, old_version, snapshot = True):
        try:
            logger.info("Compare: %s, %s" % (new_version, old_version))
            self.new_version = FolderScanner(new_version).scan(snapshot)
            self.old_version = FolderScanner(old_version).scan(snapshot)
        except FolderNotExistsException as e:
            raise e

    def scan(self):
        f = open(CHANGELOG, 'w')
        diff = {}
        for key, value in sorted(self.new_version.items()):
            new_file_hash = value
            try:
                old_file_hash = self.old_version[key]
                if new_file_hash != old_file_hash:
                    diff[key] = "U"
                    s = "%s %s \n" % ('[U]', key)
                    logger.debug(s)
                    f.write(s)
                else:
                    pass
                    #s = "%s %s \n" % ('[ ]', key)
                    #f.write(s)
            except KeyError:
                diff[key] = "+"
                s = "%s %s \n" % ('[+]', key)
                logger.debug(s)
                f.write(s)
        
        for key in sorted(self.old_version):
            if not key in self.new_version:
                diff[key] = "-"
                s = "%s %s \n" % ('[-]', key)
                logger.debug(s)
                f.write(s)
        
        f.close()
        logger.info("Compare completed")
        
        return diff
        
class FolderScanner(object):
    """
    scan specify folder and calc each file sha-1.
    """
    def __init__(self, folder):
        self.folder = folder
        if not os.path.exists(folder):
            msg = "%s not found" % folder
            logger.error(msg)
            raise FolderNotExistsException(msg)
        logger.info("scan folder: %s" % folder)

    """
    snapshot = True
    lookup files.snapshot before rescan all files.
    snapshot = False
    rescan all file and rebuild files.snapshot
    """
    def scan(self, snapshot = True):
        file_versions = {}
        rootlen = len(self.folder)
        
        # lookup snapshot before scan
        if snapshot:
            if os.path.exists(self.folder + SNAPSHOT):
                fmeta = open(self.folder + SNAPSHOT, 'r')
                file_version = ast.literal_eval(fmeta.read())
                fmeta.close()
                logger.debug("folder: %s , scan mode: %s" % (self.folder, "snapshot"))
                return file_version
        logger.debug("folder: %s , scan mode: %s" % (self.folder, "deep"))
        i = 0
        for base, dirs, files in os.walk(self.folder):
            for file in files:
                (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(base+'/'+file)
                file_meta = FileMeta(base, base.replace(self.folder, ''), file, size)
                file_versions[file_meta.relative_path] = file_meta.hash
        # build files.snapshot after scan
        fmeta = open(self.folder + SNAPSHOT, 'w')            
        fmeta.write(str(file_versions))
        fmeta.close()
        logger.info("scan folder: %s completed" % self.folder)
        return file_versions

import sys    
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "========================================="
        print "= Usage: d:\\filemonitor.py new_version_path old_version_path" 
        print "= Default: filemonitor.py D:\\python_project\\FingerPrint\\release D:\\python_project\\FingerPrint\\Genecodev3.0.25"
        print "========================================="
        new_path = 'D:\\python_project\\ReleaseRepository\\Genecodev3.0.31'
        old_path = 'D:\\python_project\\ReleaseRepository\\Genecodev3.0.30'
    else:
        new_path = sys.argv[1]
        old_path = sys.argv[2]
    x = DiffScanner(new_path, old_path, snapshot = True)
    x.scan()
    os.system("start " + CHANGELOG)
