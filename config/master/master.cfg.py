# -*- python -*-
# ex: set syntax=python:

import functools
import imp
import json
import os
import pprint
import re

from buildbot import worker
from buildbot import locks
from buildbot import util
from buildbot.plugins import util
from buildbot.schedulers import basic
from buildbot.schedulers import filter
from buildbot.schedulers import forcesched
from buildbot.schedulers import timed

from strawberry import builders

LINUX_FACTORIES = {
  'opensuse': functools.partial(builders.MakeRPMBuilder, 'opensuse'),
  'fedora': functools.partial(builders.MakeRPMBuilder, 'fedora'),
  'mageia': functools.partial(builders.MakeRPMBuilder, 'mageia'),
  'centos': functools.partial(builders.MakeRPMBuilder, 'centos'),
  'debian': functools.partial(builders.MakeDebBuilder, 'debian'),
  'ubuntu': functools.partial(builders.MakeDebBuilder, 'ubuntu'),
  'archlinux': functools.partial(builders.MakePacmanBuilder, 'archlinux'),
}

CONFIG = json.load(open('/config/config.json'))
PASSWORDS = json.load(open('/config/secret/passwords.json'))
#GITHUB_AUTH = json.load(open('/config/secret/github-auth.json'))
PPA_STABLE = 'ppa:jonaski/strawberry'
PPA_UNSTABLE = 'ppa:jonaski/strawberry-unstable'

class StrawberryBuildbot(object):
  def __init__(self):
    self.workers = []
    self.builders = []
    self.auto_builder_names = []
    self.local_builder_lock = locks.MasterLock("local", maxCount=2)
    self.deps_lock = locks.WorkerLock("deps", maxCount = 1)

    # Add Linux workers and builders.
    for linux_distro, versions in CONFIG['linux'].items():
      factory = LINUX_FACTORIES[linux_distro]
      for version in versions:
        self._AddBuilderAndWorker(linux_distro, version, factory)

    # Add Ubuntu PPA.
    for linux_distro in CONFIG['linux']['ubuntu']:
      self._AddBuilder(name='Ubuntu Stable PPA %s' % linux_distro.title(), worker='ubuntu-%s' % linux_distro, build_factory=builders.MakePPABuilder(linux_distro, "stable", PPA_STABLE))
      self._AddBuilder(name='Ubuntu Unstable PPA %s' % linux_distro.title(), worker='ubuntu-%s' % linux_distro, build_factory=builders.MakePPABuilder(linux_distro, "unstable", PPA_UNSTABLE))

    # Add special workers.
    for name in CONFIG['special_workers']:
      self._AddWorker(name)

    # Source.
    #self._AddBuilder(name='Source', worker='opensuse-lp152', build_factory=builders.MakeSourceBuilder())

    # AppImage.
    #self._AddBuilder(name='AppImage', worker='appimage', build_factory=builders.MakeAppImageBuilder(name=""))

    # MXE.
    #self._AddBuilder(name='MXE', worker='mingw', build_factory=builders.MakeMXEBuilder(), auto=False, deps_lock='exclusive')

    # Windows.
    #self._AddBuilder(name='Windows Release x86', worker='mingw', build_factory=builders.MakeWindowsBuilder(is_debug=False, is_64=False, with_qt6=False), deps_lock='counting')
    #self._AddBuilder(name='Windows Release x64', worker='mingw', build_factory=builders.MakeWindowsBuilder(is_debug=False, is_64=True, with_qt6=False), deps_lock='counting')
    #self._AddBuilder(name='Windows Debug x86', worker='mingw', build_factory=builders.MakeWindowsBuilder(is_debug=True, is_64=False, with_qt6=False), deps_lock='counting')
    #self._AddBuilder(name='Windows Debug x64', worker='mingw', build_factory=builders.MakeWindowsBuilder(is_debug=True, is_64=True, with_qt6=False), deps_lock='counting')

    #self._AddBuilder(name='Windows Release x86 Qt 6', worker='mingw', build_factory=builders.MakeWindowsBuilder(is_debug=False, is_64=False, with_qt6=True), deps_lock='counting')
    #self._AddBuilder(name='Windows Release x64 Qt 6', worker='mingw', build_factory=builders.MakeWindowsBuilder(is_debug=False, is_64=True, with_qt6=True), deps_lock='counting')
    #self._AddBuilder(name='Windows Debug x86 Qt 6', worker='mingw', build_factory=builders.MakeWindowsBuilder(is_debug=True, is_64=False, with_qt6=True), deps_lock='counting')
    #self._AddBuilder(name='Windows Debug x64 Qt 6', worker='mingw', build_factory=builders.MakeWindowsBuilder(is_debug=True, is_64=True, with_qt6=True), deps_lock='counting')


  def _AddBuilderAndWorker(self, distro, version, factory):
    worker = '%s-%s' % (distro, version)
    self._AddBuilder(
        name='%s %s' % (distro.title(), version.title()),
        worker=worker,
        build_factory=factory(version),
    )
    self._AddWorker(worker)

  def _AddBuilder(self, name, worker, build_factory, auto=True, local_lock=True, deps_lock=None):
    locks = []
    if local_lock:
      locks.append(self.local_builder_lock.access('counting'))
    if deps_lock is not None:
      locks.append(self.deps_lock.access(deps_lock))

    self.builders.append({
        'name':      str(name),
        'builddir':  str(re.sub(r'[^a-z0-9_-]', '-', name.lower())),
        'workername': str(worker),
        'factory':   build_factory,
        'locks':     locks,
    })

    if auto:
      self.auto_builder_names.append(name)

  def _AddWorker(self, name):
    self.workers.append(worker.Worker(str(name), PASSWORDS[name]))

  def Config(self):
    return {
      'projectName':  "Strawberry",
      'projectURL':   "https://www.strawberrymusicplayer.org/",
      'buildbotURL':  "http://localhost:8010/",
      'protocols': {
	  "pb": {
	    "port": "tcp:9989:interface=0.0.0.0"
	  }
      },
      'workers': self.workers,
      'builders': self.builders,
      'change_source': [
        builders.GitPoller("strawberry", "master"),
        builders.GitPoller("strawberry-mxe", "master"),
      ],
      'www': {
        'port': 8010,
        'authz': util.Authz(
            allowRules=[util.AnyControlEndpointMatcher(role="admins", defaultDeny=True)],
            roleMatchers=[
               util.RolesFromEmails(admins=["jonas@jkvinge.net"]),
               util.RolesFromOwner(role="owner"),
               util.RolesFromUsername(roles=["admins"], usernames=["admin"]),
            ]
        ),
        #'auth': util.GitHubAuth(GITHUB_AUTH["clientid"], GITHUB_AUTH["clientsecret"]),
        'auth': util.UserPasswordAuth({"admin": "doh!"}),
        'plugins': {
          'waterfall_view': True,
          'console_view': True,
          'grid_view': True,
          }
      },
      'schedulers': [
        basic.SingleBranchScheduler(
          name="automatic",
          change_filter=filter.ChangeFilter(project="strawberry", branch="master"),
          treeStableTimer=2*60,
          builderNames=self.auto_builder_names,
        ),
        #basic.SingleBranchScheduler(
        #  name="mxe",
        #  change_filter=filter.ChangeFilter(project="strawberry-mxe", branch="master"),
        #  treeStableTimer=2*60,
        #  builderNames=[
        #    'MXE',
        #  ],
        #),
        forcesched.ForceScheduler(
          name="force",
          builderNames=[x['name'] for x in self.builders],
          buttonName="Start Custom Build",
        ),
        #timed.Nightly(
        #  name="nightly",
        #  minute=0,
        #  branch="master",
        #  builderNames=[x['name'] for x in self.builders],
        #),
      ],
      'collapseRequests': False,
    }

BuildmasterConfig = StrawberryBuildbot().Config()
pprint.pprint(BuildmasterConfig)
