#!/usr/bin/env bash
# =============================================================================
# build_ant_cpp.sh -- Generate and build all antenna C++ targets
# Usage: ./build_ant_cpp.sh
# =============================================================================
set -euo pipefail

CSV="voacap.ant.csv"
GEN_H="antenna_data.h"
CXX="g++"
CXXFLAGS="-std=c++17 -Wall -Wextra -O2"

echo "=== Generating ${GEN_H} from ${CSV} ==="
bash gen_antenna_data.sh "${CSV}" "${GEN_H}"

echo "=== Compiling ==="
${CXX} ${CXXFLAGS} -c antenna_lookup.cpp -o antenna_lookup.o
${CXX} ${CXXFLAGS} -c antenna_demo.cpp   -o antenna_demo.o
${CXX} ${CXXFLAGS} -c antenna_dump.cpp   -o antenna_dump.o

echo "=== Linking ==="
${CXX} ${CXXFLAGS} antenna_lookup.o antenna_demo.o -o antenna_demo
${CXX} ${CXXFLAGS} antenna_lookup.o antenna_dump.o -o antenna_dump

echo "=== Build complete ==="
echo "  ./antenna_demo"
echo "  ./antenna_dump"