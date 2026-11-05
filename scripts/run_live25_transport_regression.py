"""Independent regression of the six previous output/handoff failures."""
import run_live25_small_sample as sample
sample.BID='dsh_bailian_qwen9b_live25_transport6_20261104_v5'
sample.COMPARISON='dsh_bailian_qwen9b_live25_small10_patches_20261104_v1'
sample.FILES=[
 'array-cav19_array_init_pair_sum_const.c',
 'array-cav19_array_tiling_tcpy.c',
 'array-crafted_bor1.c',
 'array-cav19_array_init_both_ends_multiple_sum.c',
 'array-cav19_array_init_nondet_vars.c',
 'array-crafted_zero_sum_const3.c',
]
if __name__=='__main__':sample.main()
