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

# E7 driver: one binary per (band width, result bits), plus the string-key build of w=64, r=7.
# xxhash.h comes from the system package (libxxhash-dev).
E7_BINS := e7_w64_r7 e7_w64_r8 e7_w64_r16 e7_w128_r7 e7_w128_r8 e7_w128_r16 e7_w64_r7_str

e7: $(E7_BINS)

e7_w%_str: e7_driver.cc
	$(CXX) $(CXXFLAGS) -DE7_STRKEYS -DE7_W=$(word 1,$(subst _r, ,$*)) -DE7_R=$(word 2,$(subst _r, ,$*)) -o $@ $<

e7_w%: e7_driver.cc
	$(CXX) $(CXXFLAGS) -DE7_W=$(word 1,$(subst _r, ,$*)) -DE7_R=$(word 2,$(subst _r, ,$*)) -o $@ $<

.PHONY: e7
