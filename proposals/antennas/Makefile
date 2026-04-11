# Compiler settings
CXX      := g++
CXXFLAGS := -Wall -Wextra -std=c++17

# Targets
TARGET1   := antenna_test
TARGET2   := antenna_dump

# Sources and generated files
SRCS     := antenna_lookup.cpp antenna_test.cpp antenna_dump
OBJS1    := antenna_lookup.o antenna_test.o
OBJS2    := antenna_lookup.o antenna_dump.o
GEN_HDR  := antenna_data.h
GEN_PY   := antenna_data.py

# Default target builds both the binary and the Python file
all: $(TARGET1) $(TARGET2) $(GEN_PY)

# Generate the C header from the CSV
$(GEN_HDR): voacap.ant.csv
	./gen_antenna_data.sh voacap.ant.csv $(GEN_HDR)

# Generate the Python file from the CSV
$(GEN_PY): voacap.ant.csv
	python3 gen_antenna_data.py voacap.ant.csv

# Compile object files — depend on generated header and the static header
%.o: %.cpp $(GEN_HDR) antenna_lookup.h
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Link
$(TARGET1): $(OBJS1)
	$(CXX) $(CXXFLAGS) $^ -o $@

# Link
$(TARGET2): $(OBJS2)
	$(CXX) $(CXXFLAGS) $^ -o $@


# Clean
clean:
	rm -f $(OBJS1) $(OBJS2) $(TARGET1) $(TARGET2) $(GEN_HDR) $(GEN_PY)

.PHONY: all clean
