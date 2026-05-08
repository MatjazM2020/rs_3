#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <stddef.h>
#include <stdint.h>
#include <riscv_vector.h>
#include <gem5/m5ops.h>


#define SEQ_LEN 256
#define D_K 64
#define SCALE 0.125f  // 1/sqrt(64)

/**
 * Scalar implementation of scaled dot-product attention scores.
 * Computes the dot product between query and key vectors.
 */
float dot_product_scalar(float *q, float *k, int dim) {
    float result = 0.0f;
    for (int i = 0; i < dim; i++) {
        result += q[i] * k[i];
    }
    return result;
}

/**
 * Vectorized implementation using RVV intrinsics.
 * Strip-mining pattern with m8 grouping for maximum VLEN utilization.
 */
float dot_product_vector(float *q, float *k, size_t dim) {
    size_t vl;
    /* Accumulator register: m1 group, zero-initialized */
    vfloat32m1_t vacc = __riscv_vfmv_v_f_f32m1(0.0f, 1);

    /* Use m8 grouping to maximize VLEN utilization per strip */
    vfloat32m8_t vsum = __riscv_vfmv_v_f_f32m8(0.0f, __riscv_vsetvlmax_e32m8());

    for (size_t i = 0; i < dim; i += vl) {
        vl = __riscv_vsetvl_e32m8(dim - i);

        vfloat32m8_t vq = __riscv_vle32_v_f32m8(q + i, vl);
        vfloat32m8_t vk = __riscv_vle32_v_f32m8(k + i, vl);

        /* Accumulate partial products into vsum */
        vsum = __riscv_vfmacc_vf_f32m8(vsum, 1.0f,
               __riscv_vfmul_vv_f32m8(vq, vk, vl), vl);
    }

    /* Reduce the m8 vector register group down to a scalar */
    vl = __riscv_vsetvlmax_e32m8();
    vacc = __riscv_vfredusum_vs_f32m8_f32m1(vsum, vacc, vl);
    return __riscv_vfmv_f_s_f32m1_f32(vacc);
}

void softmax_row(float *scores, float *output, int len) {
    float max_val = scores[0];
    for (int i = 1; i < len; i++) {
        if (scores[i] > max_val)
            max_val = scores[i];
    }

    float sum = 0.0f;
    for (int i = 0; i < len; i++) {
        output[i] = expf((scores[i] - max_val) * SCALE);
        sum += output[i];
    }

    for (int i = 0; i < len; i++) {
        output[i] /= sum;
    }
}

int main() {
    float Q[SEQ_LEN][D_K];
    float K[SEQ_LEN][D_K];
    float scores_scalar[SEQ_LEN];
    float scores_vector[SEQ_LEN];
    float attn_weights[SEQ_LEN];

    /* Initialize input matrices */
    for (int i = 0; i < SEQ_LEN; i++)
        for (int j = 0; j < D_K; j++) {
            Q[i][j] = (float)(i + j) * 0.01f;
            K[i][j] = (float)(i - j) * 0.01f;
        }

    /* ============================================ */
    /* Test scalar implementation                  */
    /* ============================================ */
    #ifdef GEM5
        m5_reset_stats(0, 0);
    #endif
    for (int j = 0; j < SEQ_LEN; j++)
        scores_scalar[j] = dot_product_scalar(Q[0], K[j], D_K);
    #ifdef GEM5
        m5_dump_stats(0, 0);
    #endif

    /* ============================================ */
    /* Test vectorized implementation              */
    /* ============================================ */
    #ifdef GEM5
        m5_reset_stats(0, 0);
    #endif
    for (int j = 0; j < SEQ_LEN; j++)
        scores_vector[j] = dot_product_vector(Q[0], K[j], D_K);
    #ifdef GEM5
        m5_dump_stats(0, 0);
    #endif

    /* Verify correctness: scalar vs vectorized */
    int all_match = 1;
    for (int i = 0; i < SEQ_LEN; i++) {
        float diff = fabsf(scores_scalar[i] - scores_vector[i]);
        if (diff > 1e-5f) {
            printf("Mismatch at index %d: scalar=%.6f, vector=%.6f, diff=%.6e\n", 
                   i, scores_scalar[i], scores_vector[i], diff);
            all_match = 0;
        }
    }

    if (all_match) {
        printf("✓ All results match between scalar and vectorized implementations.\n");
    } else {
        printf("✗ Results differ between scalar and vectorized implementations.\n");
        return 1;
    }

    /* Apply softmax to vectorized results */
    softmax_row(scores_vector, attn_weights, SEQ_LEN);

    printf("First 4 attention weights:\n");
    for (int i = 0; i < 4; i++)
        printf("attn[%d] = %.6f\n", i, attn_weights[i]);

    return 0;
}