import os
from tempfile import mkdtemp
from fabric.api import cd, local, put, run, sudo

def upload_project(local_dir=None, remote_dir="", use_sudo=False):
    """
    Upload the current project to a remote system via ``tar``/``gzip``.

    ``local_dir`` specifies the local project directory to upload, and defaults
    to the current working directory.

    ``remote_dir`` specifies the target directory to upload into (meaning that
    a copy of ``local_dir`` will appear as a subdirectory of ``remote_dir``)
    and defaults to the remote user's home directory.

    This function makes use of the ``tar`` and ``gzip`` programs/libraries,
    thus it will not work too well on Win32 systems unless one is using Cygwin
    or something similar. It will attempt to clean up the local and remote
    tarfiles when it finishes executing, even in the event of a failure.

    .. versionchanged:: 1.1
        Added the ``local_dir`` and ``remote_dir`` kwargs.
    """
    remote_exe = use_sudo and sudo or run

    local_dir = local_dir or os.getcwd()

    # Remove final '/' in local_dir so that basename() works
    local_dir = local_dir.rstrip(os.sep)

    local_path, local_name = os.path.split(local_dir)
    tar_file = "%s.tar.gz" % local_name
    target_tar = os.path.join(remote_dir, tar_file)
    tmp_folder = mkdtemp()

    try:
        tar_path = os.path.join(tmp_folder, tar_file)
        local("tar -czf %s -C %s %s" % (tar_path, local_path, local_name))
        put(tar_path, target_tar, use_sudo=use_sudo)
        with cd(remote_dir):
            try:
                remote_exe("tar -xzf %s" % tar_file)
            finally:
                remote_exe("rm -f %s" % tar_file)
    finally:
        local("rm -rf %s" % tmp_folder)

class ProjectInfo(object):
    """
    Manages common paths locally and remotely.
    """
    def __init__(self, project_name, local_top, remote_top='/opt', remote_temp_top='/tmp', virtual_environment_top='/opt/virtualenvs'):
        """
        Remote paths will contain 'remote_top' and 'project_name' usually.
        Only temporary files will be exluded from this.
        Temporary files will be created under 'remote_temp_top' remotely.

        Local paths will contain 'local_top' only.
        """
        self.project_name = project_name
        self.local_top = local_top
        self.remote_top = remote_top
        self.remote_temp_top = remote_temp_top
        self.temp_directory = self.remote_temp_top
        self.virtual_environment_top = virtual_environment_top
        self.__subprojects = []

    @property
    def subprojects(self):
        if not self.__subprojects:
            root = self.local_project_directory
            self.__subprojects = filter(lambda x: not x.startswith('.'),
                map(
                    lambda dirpath: os.path.basename(dirpath),
                    filter(
                        os.path.isdir,
                        map(lambda filename: os.path.join(root, filename), os.listdir(root)))))
        return self.__subprojects

    @property
    def local_thirdparty_directory(self):
        """
        Location of thirdparty modules locally.
        """
        return '%s/thirdparty' % self.local_top

    @property
    def local_project_directory(self):
        return '%s/projects' % self.local_top

    @property
    def project_directory(self):
        """
        Location of project directory remotely.
        """
        return '%s/projects/%s' % (self.remote_top, self.project_name)

    @property
    def virtual_environment(self):
        """
        Location of virtual environment remotely.
        """
        return os.path.join(self.virtual_environment_top, self.project_name)

    def get_subproject_directory(self, subproject):
        """
        Location of subproject directory remotely.
        """
        return '%s/%s' % (self.project_directory, subproject)
