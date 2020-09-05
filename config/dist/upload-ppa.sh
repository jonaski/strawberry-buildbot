#!/bin/sh

ppa_type=$1
ppa_path=$2
git_revision=$(sed -n 's/^set(INCLUDE_GIT_REVISION \(.*\))/\1/p' source/cmake/Version.cmake)

if [ "$ppa_type" = "" ] || [ "$ppa_path" = "" ] || [ "$git_revision" = "" ]; then
  echo "$0 - Missing config."
  exit 1
fi

if [ "$git_revision" = "OFF" ] || [ "$ppa_type" = "unstable" ]; then
  echo "Uploading PPA for ${ppa_type} path ${ppa_path}..."
  dput $ppa_path *_source.changes
else
  echo "Not uploading PPA for ${ppa_type} path ${ppa_path}."
fi
