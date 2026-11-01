#include<limits.h>

/*@ axiomatic Sum {
    logic integer sum_arr{L}(int *a, integer lo, integer hi) reads a[lo..hi-1];

    axiom sum_empty{L}: \forall int *a, integer lo, hi;
        hi <= lo ==> sum_arr{L}(a, lo, hi) == 0;

    axiom sum_next{L}: \forall int *a, integer lo, hi;
        lo < hi ==>
        sum_arr{L}(a, lo, hi) == sum_arr{L}(a, lo, hi-1) + \at(a[hi-1], L);

    axiom sum_one{L}: \forall int *a, integer k;
        sum_arr{L}(a, k, k+1) == \at(a[k], L);

    axiom sum_prepend{L}: \forall int *a, integer lo, hi;
        lo < hi ==>
        sum_arr{L}(a, lo, hi) == \at(a[lo], L) + sum_arr{L}(a, lo+1, hi);

    axiom sum_frame{L1,L2}: \forall int *a, integer lo, hi;
        (\forall integer k; lo <= k < hi ==> \at(a[k],L1) == \at(a[k],L2)) ==>
        sum_arr{L1}(a, lo, hi) == sum_arr{L2}(a, lo, hi);

    axiom sum_shift{L1,L2}: \forall int *a, integer lo, hi;
        lo < hi ==>
        (\forall integer k; lo <= k < hi ==> \at(a[k],L2) == \at(a[k+1],L1)) ==>
        sum_arr{L2}(a, lo, hi) == sum_arr{L1}(a, lo+1, hi+1);
} */

/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown(void);
#define N 10000
#define fun mapavg
#include <assert.h>

/*@
  requires \valid_read(x+(0..9999));
  requires \forall integer i; 0 <= i < 10000 ==> INT_MIN <= x[i] < INT_MAX;
  assigns \nothing;
  ensures \result == (int)((49995000 + sum_arr(x, 0, 10000)) / 10000);
*/
int mapavg (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= 10000;
    loop invariant ret == i*(i-1)/2 + sum_arr(x, 0, i);
    loop assigns i, ret;
    loop variant 10000 - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret+ i + x[i];
  }
  return ret / N;
}
int main (void)
{
  int x[N];
  int temp;
  int ret;
  int ret2;
  int ret5;
  int *px = &x[0];
  /*@
    loop invariant 0 <= i <= 10000;
    loop invariant \forall integer j; 0 <= j < i ==> INT_MIN <= px[j] < INT_MAX;
    loop assigns i, x[0..9999];
    loop variant 10000 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  Pre_swap: ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert sum_arr(px, 0, 1) == px[0];
  //@ assert sum_arr(px, 1, 2) == px[1];
  //@ assert sum_arr(px, 0, 2) == px[0] + px[1];
  //@ assert px[0] + px[1] == \at(px[0], Pre_swap) + \at(px[1], Pre_swap);
  //@ assert \forall integer k; 2 <= k < 10000 ==> px[k] == \at(px[k], Pre_swap);
  //@ assert sum_arr(px, 2, 10000) == sum_arr{Pre_swap}(px, 2, 10000);
  //@ assert sum_arr{Pre_swap}(px, 0, 1) == \at(px[0], Pre_swap);
  //@ assert sum_arr{Pre_swap}(px, 1, 2) == \at(px[1], Pre_swap);
  //@ assert sum_arr{Pre_swap}(px, 0, 2) == \at(px[0], Pre_swap) + \at(px[1], Pre_swap);
  //@ assert sum_arr(px, 0, 10000) == px[0] + sum_arr(px, 1, 10000);
  //@ assert sum_arr(px, 1, 10000) == px[1] + sum_arr(px, 2, 10000);
  //@ assert sum_arr(px, 0, 10000) == px[0] + px[1] + sum_arr(px, 2, 10000);
  //@ assert sum_arr{Pre_swap}(px, 0, 10000) == \at(px[0], Pre_swap) + sum_arr{Pre_swap}(px, 1, 10000);
  //@ assert sum_arr{Pre_swap}(px, 1, 10000) == \at(px[1], Pre_swap) + sum_arr{Pre_swap}(px, 2, 10000);
  //@ assert sum_arr{Pre_swap}(px, 0, 10000) == \at(px[0], Pre_swap) + \at(px[1], Pre_swap) + sum_arr{Pre_swap}(px, 2, 10000);
  //@ assert sum_arr(px, 0, 10000) == sum_arr{Pre_swap}(px, 0, 10000);
  ret2 = fun(x);
  Pre_rot: temp=x[0];
  /*@
    loop invariant 0 <= i <= 9999;
    loop invariant \forall integer j; 0 <= j < i ==> px[j] == \at(px[j+1], Pre_rot);
    loop invariant \forall integer j; i <= j < 10000 ==> px[j] == \at(px[j], Pre_rot);
    loop invariant temp == \at(px[0], Pre_rot);
    loop assigns i, x[0..9998];
    loop variant 9999-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert \forall integer j; 0 <= j < 9999 ==> px[j] == \at(px[j+1], Pre_rot);
  //@ assert px[9999] == \at(px[0], Pre_rot);
  //@ assert sum_arr(px, 0, 9999) == sum_arr{Pre_rot}(px, 1, 10000);
  //@ assert sum_arr(px, 9999, 10000) == px[9999];
  //@ assert sum_arr{Pre_rot}(px, 0, 1) == \at(px[0], Pre_rot);
  //@ assert sum_arr(px, 9999, 10000) == sum_arr{Pre_rot}(px, 0, 1);
  //@ assert sum_arr(px, 0, 10000) == sum_arr(px, 0, 9999) + sum_arr(px, 9999, 10000);
  //@ assert sum_arr{Pre_rot}(px, 0, 10000) == \at(px[0], Pre_rot) + sum_arr{Pre_rot}(px, 1, 10000);
  //@ assert sum_arr(px, 0, 10000) == sum_arr{Pre_rot}(px, 1, 10000) + sum_arr{Pre_rot}(px, 0, 1);
  //@ assert sum_arr(px, 0, 10000) == sum_arr{Pre_rot}(px, 0, 10000);
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
