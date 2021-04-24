#! /usr/bin/bash

# This script was automatically generated on
# <GENERATED>

if [[ ! -d "<PEANO>" ]]
then
	echo "ERROR: Peano directory not found" > /dev/stderr
	exit 1
fi

module purge
module load intel/2020.4
module load intelmpi/intel/2019.6
module load python/3.6.8
module remove gcc
module load gcc/9.3.0

export CC=icc
export CXX=icpc

echo Loaded modules:
module list -l

echo cd <PEANO>/examples/exahype2/euler
cd <PEANO>/examples/exahype2/euler

python3 example-scripts/finitevolumes-with-ExaHyPE2-benchmark.py \
    -o  <ROOT>/<EXPERIMENT>/<EXE> \
    -m  <MODE> \
    -t  <TYPE> \
    -cs <CELLSIZE> \
    -d  <DIM> \
    -ps <PS> \
    -et <ENDTIME> \
    -j  <J> \
    -f
