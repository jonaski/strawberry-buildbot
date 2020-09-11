#!/bin/sh

strip_cmd=$1

if [ "$strip_cmd" = "" ]; then
  echo "$0 - Missing config."
  exit 1
fi

for i in $(find . -type f \( -iname \*.dll -o -iname \*.exe \))
do
    echo "Stripping $i"
    echo "$strip_cmd $i"
    $strip_cmd $i
done
