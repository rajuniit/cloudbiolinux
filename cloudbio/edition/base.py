"""Base editions supplying CloudBioLinux functionality which can be customized.

These are a set of testing and supported edition classes.
"""
from fabric.api import *

from cloudbio.cloudman import _configure_cloudman
from cloudbio.cloudbiolinux import _freenx_scripts

class Edition:
    """Base class. Every edition derives from this
    """
    def __init__(self, env):
        self.name = "BioLinux base Edition"
        self.short_name = "biolinux"
        self.version = env.version
        self.env = env
        self.check_distribution()

    def check_distribution(self):
        """Ensure the distribution matches an expected type for this edition.

        Base supports multiple distributions.
        """
        pass

    def check_packages_source(self):
        """Override for check package definition file before updating
        """
        pass

    def rewrite_apt_sources_list(self, sources):
        """Allows editions to modify the sources list
        """
        return sources

    def rewrite_apt_preferences(self, preferences):
        """Allows editions to modify the apt preferences policy file
        """
        return preferences

    def rewrite_apt_automation(self, package_info):
        """Allows editions to modify the apt automation list
        """
        return package_info

    def rewrite_apt_keys(self, standalone, keyserver):
        """Allows editions to modify key list"""
        return standalone, keyserver

    def apt_upgrade_system(self, env=None):
        """Upgrade system through apt - so this behaviour can be overridden
        """
        sudo_cmd = env.safe_sudo if env else sudo
        sudo_cmd("apt-get -y --force-yes upgrade")

    def post_install(self, pkg_install=None):
        """Post installation hook"""
        pass

    def rewrite_config_items(self, name, items):
        """Generic hook to rewrite a list of configured items.

        Can define custom dispatches based on name: packages, custom,
        python, ruby, perl
        """
        return items

class CloudBioLinux(Edition):
    """Specific customizations for CloudBioLinux builds.
    """
    def __init__(self, env):
        Edition.__init__(self,env)
        self.name = "CloudBioLinux Edition"
        self.short_name = "cloudbiolinux"

    def rewrite_config_items(self, name, items):
        """Generic hook to rewrite a list of configured items.

        Can define custom dispatches based on name: packages, custom,
        python, ruby, perl
        """
        to_add = ["galaxy", "galaxy_tools", "cloudman"]
        for x in to_add:
            if x not in items:
                items.append(x)
        return items

    def post_install(self, pkg_install=None):
        """Add scripts for starting FreeNX and CloudMan.
        """
        _freenx_scripts(self.env)
        if pkg_install is not None and 'cloudman' in pkg_install:
            _configure_cloudman(self.env)

class BioNode(Edition):
    """BioNode specialization of BioLinux
    """
    def __init__(self, env):
        Edition.__init__(self,env)
        self.name = "BioNode Edition"
        self.short_name = "bionode"

    def check_distribution(self):
        # if self.env.distribution not in ["debian"]:
        #    raise ValueError("Distribution is not pure Debian")
        pass

    def check_packages_source(self):
        # Bionode always removes sources, just to be sure
        self.env.logger.debug("Clearing %s" % self.env.sources_file)
        sudo("cat /dev/null > %s" % self.env.sources_file)

    def rewrite_apt_sources_list(self, sources):
        """BioNode will pull packages from Debian 'testing', if not
           available in stable. Also BioLinux packages are included.
        """
        self.env.logger.debug("BioNode.rewrite_apt_sources_list!")
        new_sources = []
        if self.env.distribution in ["debian"]:
          # See if the repository is defined in env
          if not env.get('debian_repository'):
              main_repository = 'http://ftp.us.debian.org/debian/'
          else:
              main_repository = env.debian_repository
          # The two basic repositories
          new_sources += ["deb {repo} {dist} main contrib non-free".format(repo=main_repository,
                                                                          dist=env.dist_name),
                         "deb {repo} {dist}-updates main contrib non-free".format(
                             repo=main_repository, dist=env.dist_name),
                         "deb {repo} testing main contrib non-free".format(
                             repo=main_repository)
                        ]
        new_sources = new_sources + [ "deb http://nebc.nerc.ac.uk/bio-linux/ unstable bio-linux" ]

        return new_sources

    def rewrite_apt_preferences(self, preferences):
        """Allows editions to modify apt preferences (load order of
        packages, i.e. the package dowload policy. Here we use
        'stable' packages, unless only available in 'testing'.
        """
        preferences = """Package: *
Package: *
Pin: release n=natty
Pin-Priority: 900

Package: *
Pin: release a=stable
Pin-Priority: 700

Package: *
Pin: release a=testing
Pin-Priority: 650

Package: *
Pin: release a=bio-linux
Pin-Priority: 400
"""
        return preferences.split('\n')

    def rewrite_apt_automation(self, package_info):
        return []

    def rewrite_apt_keys(self, standalone, keyserver):
        return [], []

    def rewrite_config_items(self, name, items):
        # BioLinux add keyring
        if name == 'minimal':
            return items + [ 'bio-linux-keyring' ]
        return items

class Minimal(Edition):
    """Minimal specialization of BioLinux
    """
    def __init__(self, env):
        Edition.__init__(self, env)
        self.name = "Minimal Edition"
        self.short_name = "minimal"

    def rewrite_apt_sources_list(self, sources):
        """Allows editions to modify the sources list. Minimal, by
           default, assumes system has stable packages configured
           and adds only the biolinux repository.
        """
        return ["deb http://nebc.nerc.ac.uk/bio-linux/ unstable bio-linux"]

    def rewrite_apt_automation(self, package_info):
        return []

    def rewrite_apt_keys(self, standalone, keyserver):
        return [], []

    def apt_upgrade_system(self, env=None):
        """Do nothing"""
        env.logger.debug("Skipping forced system upgrade")

    def rewrite_config_items(self, name, items):
        """Generic hook to rewrite a list of configured items.

        Can define custom dispatches based on name: packages, custom,
        python, ruby, perl
        """
        return items
