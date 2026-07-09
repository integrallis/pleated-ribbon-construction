# E1b Phase-1 driver. Compiles against the pinned, unmodified fastfilter_cpp headers.
HARNESS := ../../harness/fastfilter_cpp
CXX ?= g++
CXXFLAGS := -O3 -march=native -std=c++17 -Wall -Wextra -pthread \
            -I$(HARNESS)/src/ribbon -I$(HARNESS)/benchmarks -I../../harness/BuRR/ips2ra/include -isystem /home/linuxbrew/.linuxbrew/include

e1b_phase1: e1b_phase1.cc
	$(CXX) $(CXXFLAGS) -o $@ $<

clean:
	rm -f e1b_phase1

.PHONY: clean
