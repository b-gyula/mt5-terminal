#!/bin/bash
# Copyright 2000-2026, MetaQuotes Ltd.

# Wine version to install: stable or devel
WINE_VER=staging #10.2

if [ "$1" = "-u" ] ; then
    echo "Update Wine"
    WINE_PKGS=$(dpkg -l | grep -i wine | awk '{print $2}')
    if [ -n "$WINE_PKGS" ]; then
        echo "Removing installed wine packages:$WINE_PKGS"
        apt remove --purge $WINE_PKGS -y
    fi
    shift
fi

[ -n "$1" ] && WINE_VER=$1
# Prepare versions

. /etc/os-release

echo OS: $NAME $VERSION_ID

echo Update and install Wine $WINE_VER
if [ "$NAME" = "Fedora Linux" ]; then
    echo Update system
    dnf update
    dnf upgrade -y

    if [ ! -f /etc/yum.repos.d/winehq* ]; then
      echo Choose Wine repo
      if (( $VERSION_ID >= 43 )); then
         dnf config-manager addrepo --from-repofile=https://dl.winehq.org/wine-builds/fedora/43/winehq.repo
      elif (( $VERSION_ID < 43 && $VERSION_ID >= 42 )); then
         dnf config-manager addrepo --from-repofile=https://dl.winehq.org/wine-builds/fedora/42/winehq.repo
      else
         dnf config-manager addrepo --from-repofile=https://dl.winehq.org/wine-builds/fedora/41/winehq.repo
      fi
    fi
    echo Install Wine $WINE_VER and Wine Mono
    dnf update
    dnf install winehq-$WINE_VER -y
    dnf install wine-mono -y
else
    echo Update system
    apt update
    apt upgrade -y
    if [ ! -f /etc/apt/sources.list.d/winehq* ]; then
      echo Get full version
      apt install bc wget curl pgpgpg -y
      VERSION_FULL=$(echo "$VERSION_ID * 100" | bc -l | cut -d "." -f1)
      echo Choose Wine repo

      dpkg --add-architecture i386
      mkdir -pm755 /etc/apt/keyrings
      # Download and import the WineHQ GPG key properly
      wget -qO- https://dl.winehq.org/wine-builds/winehq.key | gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key -
      #chmod 644 /etc/apt/keyrings/winehq-archive.key

      if [ "$NAME" = "Ubuntu" ]; then
         echo Ubuntu found: $NAME $VERSION_ID
         # Choose repository based on Ubuntu version
         if (( $VERSION_FULL >= 2510 )); then
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/questing/winehq-questing.sources
         elif (( $VERSION_FULL < 2510 )) && (( $VERSION_FULL >= 2504 )); then
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/plucky/winehq-plucky.sources
         elif (( $VERSION_FULL < 2410 )) && (( $VERSION_FULL >= 2400 )); then
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/noble/winehq-noble.sources
         elif (( $VERSION_FULL < 2400 )) && (( $VERSION_FULL >= 2300 )); then
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/lunar/winehq-lunar.sources
         elif (( $VERSION_FULL < 2300 )) && (( $VERSION_FULL >= 2210 )); then
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/kinetic/winehq-kinetic.sources
         elif (( $VERSION_FULL < 2210 )) && (( $VERSION_FULL >= 2100 )); then
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/jammy/winehq-jammy.sources
         elif (( $VERSION_FULL < 2100 )) && (($VERSION_FULL >= 2000 )); then
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/focal/winehq-focal.sources
         else
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/bionic/winehq-bionic.sources
         fi
      elif [ "$NAME" = "Linux Mint" ]; then
         echo Linux Mint found: $NAME $VERSION_ID
         # Choose repository based on Linux Mint version
         if (( $VERSION_FULL >= 2200 )); then
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/noble/winehq-noble.sources
         else
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/focal/winehq-focal.sources
         fi
      elif [ "$NAME" = "Debian GNU/Linux" ]; then
         echo Debian Linux found: $NAME $VERSION_ID
         # Choose repository based on Debian version
         if (( $VERSION_FULL >= 13 )); then
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/trixie/winehq-trixie.sources
         else
            wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/debian/dists/bookworm/winehq-bookworm.sources
         fi
      else
         echo $NAME $VERSION_ID not supported
         exit
      fi
    fi
    echo Install Wine "$WINE_VER" and Wine Mono
    apt update
    apt install --install-recommends --allow-downgrades winehq-$WINE_VER -y
fi
echo Wine $(wine --version) installed
