#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <riscv_vector.h>
// Include the gem5 m5ops header file
#include <gem5/m5ops.h>
#define HIST_BINS  256       /* histogram bins */                
 
void histogram_scalar(const uint8_t *data, uint32_t *hist, size_t n) {
    memset(hist, 0, HIST_BINS * sizeof(uint32_t));
    for (size_t i = 0; i < n; i++)
        hist[data[i]]++;
}
 
void histogram_rvv(const uint8_t *data, uint32_t *hist, size_t n) {
    memset(hist, 0, HIST_BINS * sizeof(uint32_t));
    size_t vl;
    for (size_t i = 0; i < n; i += vl) {
        vl = __riscv_vsetvl_e8m1(n - i);
 
        /* Load vl bytes */
        vuint8m1_t  vbytes = __riscv_vle8_v_u8m1(data + i, vl);
 
        /* Widen to 32-bit to use as indices */
        vuint32m4_t vidx   = __riscv_vzext_vf4_u32m4(vbytes, vl);
 
        /*
        * No vectorised scatter-add in RVV 1.0:
        */
        for (size_t k = 0; k < vl; k++) {
            /* Extract scalar index from vector register */
            uint32_t idx = __riscv_vmv_x_s_u32m4_u32(
                               __riscv_vslidedown_vx_u32m4(vidx, k, vl));
            hist[idx]++;
        }
    }
}

int main() {
    const size_t n = 1 << 15; // Example data length
    uint8_t data[n];
    uint32_t hist_scalar[HIST_BINS], hist_rvv[HIST_BINS];
 
    // Initialize data with example values (e.g., random bytes)
    for (size_t i = 0; i < n; i++) {
        data[i] = rand() % HIST_BINS;
    }
 
    #ifdef GEM5
        m5_work_begin(0, 0);
    #endif
    histogram_scalar(data, hist_scalar, n);
    #ifdef GEM5
        m5_work_end(0, 0);
    #endif
 
    #ifdef GEM5
        m5_work_begin(0, 0);
    #endif
    histogram_rvv(data, hist_rvv, n);
    #ifdef GEM5
        m5_work_end(0, 0);
    #endif
 
    // Print the histogram (optional)
    printf("Histogram:\n");
    for (size_t i = 0; i < HIST_BINS; i++) {
        printf("Bin %zu: %u\n", i, hist_scalar[i]);
    }
 
    return 0;
}