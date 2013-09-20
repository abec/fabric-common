import os
import sys


def auto_sync(local_paths=[], remote_path=None, use_sudo=False, timeout=1):
    assert local_paths, "please provide non-empty list of local paths"
    assert remote_path, "please provide remote_path to push content to"
    files_changed = FilesChanged(paths)
    while True:
        for filepath in files_changed():
            relpath = os.path.relpath(filepath)
            put(relpath,
                remote_path=os.path.join(remote_path, relpath),
                use_sudo=use_sudo)
        time.sleep(timeout)

class FilesChanged(object):
    """
    Figures out which files have changed the following way:
    1. Remember mtimes for directories.
    2. Remember mtimes for files.
    3. If directory mtime has changed, there is a new file. List directory contents and remember file mtimes.
    4. If file mtime has changed, return file in list.
    """

    def __init__(self, directories=[]):
        """
        Remember mtimes for all files and directories within 'directories'.
        """
        self.mtimes_files = {}
        self.mtimes_dirs = {}
        self.win = sys.platform == "win32"

        for directory in directories:
            self.add_directory(directory)

    def __call__(self):
        """
        See 'FilesChanged.has_changed'.
        """
        return self.has_changed()

    def add_directory(self, dirpath):
        """
        Find all files and directories within a directory and remember their mtimes.
        Returns a list of files added within 'dirpath'.
        """
        added = []
        for root, dirnames, filenames in os.walk(dirpath):
            for dirname in dirnames:
                _dirpath = os.path.join(root, dirname)
                stat = os.stat(_dirpath)
                mtime = stat.st_mtime
                if self.win:
                    mtime -= stat.st_ctime
                if _dirpath not in self.mtimes_dirs:
                    self.mtimes_dirs[_dirpath] = mtime
                    added.append(_dirpath)
                elif mtime != self.mtimes_dirs[_dirpath]:
                    added.append(_dirpath)
            for filename in filenames:
                filepath = os.path.join(root, filename)
                self.add_file(filepath)
                added.append(filepath)
        return added

    def add_file(self, filepath):
        """
        Format 'filepath' so that it is a non-python compiled file.
        Remember mtime of 'filepath'.
        """
        # Transform compiled python files to normal python files.
        if filepath.endswith(".pyc") or filepath.endswith(".pyo"):
            filepath = filepath[:-1]
        if filepath.endswith("$py.class"):
            filepath = filepath[:-9] + ".py"
        if os.path.exists(filepath):
            stat = os.stat(filepath)
            mtime = stat.st_mtime
            if self.win:
                mtime -= stat.st_ctime
            if filepath not in self.mtimes_files:
                self.mtimes_files[filepath] = mtime

    def changed_in_directory(self, dirpath):
        """
        When a new file is added to, or removed from, a directory, the parent directory's mtime changes.
        Find which files have been added or removed.
        If a directory is added, add its children as well through 'FilesChanged.add_directory'.
        Returns a list of paths that have been changed within the provided 'dirpath' (whether it be deleted, added, or modified).
        """
        changed = []
        for filename in os.listdir(dirpath):
            filepath = os.path.join(directory, filename)
            if os.path.isdir(filepath):
                if filepath not in self.mtimes_dirs:
                    changed.append(filepath)
                    changed.extend(self.add_directory(filepath))
            else:
                if filepath not in self.mtimes_files:
                    self.add_file(filepath)
                    changed.append(filepath)
        return changed

    def has_changed(self):
        """
        Return a list of paths that have recently changed in some way (whether it be deleted, added, or modified).
        """
        changed = []

        # All changed directories will update mtimes for immediate children files.
        # Will also return changed child files in changed list.
        for dirpath in self.mtimes_dirs:
            stat = os.stat(dirpath)
            mtime = stat.st_mtime
            if self.win:
                mtime -= stat.st_ctime
            if mtime != self.mtimes_dirs[dirpath]:
                self.mtimes_dirs[dirpath] = mtime
                changed.extend(self.changed_in_directory(dirpath))

        # Update the rest of the files.
        for filepath in self.mtimes_files:
            stat = os.stat(filepath)
            mtime = stat.st_mtime
            if self.win:
                mtime -= stat.st_ctime
            if mtime != self.mtimes_files[filepath]:
                self.mtimes_files[filepath] = mtime
                changed.append(filepath)

        return changed