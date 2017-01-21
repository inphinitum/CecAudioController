#!/bin/sh
set -e

if [ ! -d "$HOME/env" ]; then
  mkdir $HOME/env
fi

# Skip building if libcec is chached from previous runs.
if [ ! -d "$HOME/env/bin" ]; then

  mkdir $HOME/src/

  # Download and build Python 3.5.2
  cd $HOME/src
  wget https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz
  tar -xzf Python-3.5.2.tgz
  cd Python-3.5.2
  ./configure --prefix=$HOME/env --enable-shared
  make
  make install

  # Download and build cmake 3.0.1
  cd $HOME/src
  wget https://cmake.org/files/v3.0/cmake-3.0.1.tar.gz --no-check-certificate
  tar -xzf cmake-3.0.1.tar.gz
  cd cmake-3.0.1
  env CC=/usr/bin/gcc-4.8 CXX=/usr/bin/g++-4.8 ./bootstrap --prefix=$HOME/env
  cmake -DCMAKE_INSTALL_PREFIX=$HOME/env -DCMAKE_C_COMPILER=/usr/bin/gcc-4.8 -DCMAKE_CXX_COMPILER=/usr/bin/g++-4.8 .
  make -j2 && make install

  # Use locally compiled cmake
  export PATH=$HOME/env/bin:$PATH

  # Download and build p8-platform, needed by libcec
  cd $HOME/src
  wget https://github.com/Pulse-Eight/platform/archive/p8-platform-2.1.0.1.tar.gz
  tar -xzf p8-platform-2.1.0.1.tar.gz
  mkdir platform-p8-platform-2.1.0.1/build
  cd platform-p8-platform-2.1.0.1/build
  cmake -DCMAKE_INSTALL_PREFIX=$HOME/env -DCMAKE_C_COMPILER=/usr/bin/gcc-4.8 -DCMAKE_CXX_COMPILER=/usr/bin/g++-4.8 ..
  make install

  # Download and build libcec
  cd $HOME/src
  git clone https://github.com/inphinitum/libcec.git
  mkdir libcec/build
  cd libcec/build
  cmake -DPYTHON_LIBRARY=$HOME/env/lib/libpython3.5m.so -DPYTHON_INCLUDE_DIR=$HOME/env/include/python3.5m -DCMAKE_INSTALL_PREFIX=$HOME/env -DCMAKE_C_COMPILER=/usr/bin/gcc-4.8 -DCMAKE_CXX_COMPILER=/usr/bin/g++-4.8 ..
  make -j2 && make install && cd $HOME

else
  echo "Using cached directory."
fi