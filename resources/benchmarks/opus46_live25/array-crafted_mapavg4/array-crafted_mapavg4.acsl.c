#include<limits.h>
/*@ axiomatic ArrSum {
    logic integer arr_sum(int *a, integer lo, integer hi) reads a[lo .. hi-1];
    axiom sum_empty: \forall int *a, integer lo, hi;
      hi <= lo ==> arr_sum(a, lo, hi) == 0;
    axiom sum_step: \forall int *a, integer lo, integer hi;
      lo < hi ==> arr_sum(a, lo, hi) == arr_sum(a, lo, hi-1) + a[hi-1];
    axiom sum_split: \forall int *a, integer lo, integer mid, integer hi;
      lo <= mid <= hi ==> arr_sum(a, lo, hi) == arr_sum(a, lo, mid) + arr_sum(a, mid, hi);
    axiom sum_frame{L1, L2}: \forall int *a, integer lo, integer hi;
      (\forall integer k; lo <= k < hi ==> \at(a[k], L1) == \at(a[k], L2)) ==>
      \at(arr_sum(a, lo, hi), L1) == \at(arr_sum(a, lo, hi), L2);
    axiom sum_update{L1, L2}: \forall int *a, integer lo, integer hi, integer k;
      lo <= k < hi ==>
      (\forall integer j; lo <= j < hi && j != k ==> \at(a[j], L1) == \at(a[j], L2)) ==>
      \at(arr_sum(a, lo, hi), L2) == \at(arr_sum(a, lo, hi), L1) - \at(a[k], L1) + \at(a[k], L2);
}*/
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100000
#define fun mapavg
#include <assert.h>
/*@
  requires \valid(x + (0 .. N-1));
  assigns \nothing;
  ensures (integer)\result == (integer)((int)((((integer)N*((integer)N-1))/2 + arr_sum(x, 0, (integer)N)) / (integer)N));
*/
int mapavg (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant ret == ((integer)i*((integer)i-1))/2 + arr_sum(x, 0, (integer)i);
    loop assigns i, ret;
    loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret+ i + x[i];
  }
  return ret / N;
}
int main ()
{
  int x[N];
  int temp;
  int ret;
  int ret2;
  int ret5;
  /*@
    loop invariant 0 <= i <= N;
    loop assigns i, x[0 .. N-1];
    loop variant N - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  L_swap:
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert arr_sum(&x[0], 0, 2) == (integer)x[0] + (integer)x[1];
  //@ assert \at(arr_sum(&x[0], 0, 2), L_swap) == (integer)\at(x[0], L_swap) + (integer)\at(x[1], L_swap);
  //@ assert (integer)x[0] + (integer)x[1] == (integer)\at(x[0], L_swap) + (integer)\at(x[1], L_swap);
  //@ assert arr_sum(&x[0], 0, (integer)N) == arr_sum(&x[0], 0, 2) + arr_sum(&x[0], 2, (integer)N);
  //@ assert \at(arr_sum(&x[0], 0, (integer)N), L_swap) == \at(arr_sum(&x[0], 0, 2), L_swap) + \at(arr_sum(&x[0], 2, (integer)N), L_swap);
  //@ assert arr_sum(&x[0], 2, (integer)N) == \at(arr_sum(&x[0], 2, (integer)N), L_swap);
  //@ assert arr_sum(&x[0], 0, (integer)N) == \at(arr_sum(&x[0], 0, (integer)N), L_swap);
  ret2 = fun(x);
  //@ assert ret == ret2;
  L_rot:
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], L_rot);
    loop invariant arr_sum(&x[0], 0, (integer)N) == \at(arr_sum(&x[0], 0, (integer)N), L_rot) - (integer)temp + (integer)x[i];
    loop assigns i, x[0 .. N-2];
    loop variant N - 1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     L_body: ;
     //@ assert arr_sum(&x[0], (integer)i, (integer)i+1) == (integer)x[i];
     //@ assert arr_sum(&x[0], 0, (integer)N) == arr_sum(&x[0], 0, (integer)i) + (integer)x[i] + arr_sum(&x[0], (integer)i+1, (integer)N);
     x[i] = x[i+1];
     //@ assert arr_sum(&x[0], 0, (integer)i) == \at(arr_sum(&x[0], 0, (integer)i), L_body);
     //@ assert arr_sum(&x[0], (integer)i+1, (integer)N) == \at(arr_sum(&x[0], (integer)i+1, (integer)N), L_body);
     //@ assert arr_sum(&x[0], (integer)i, (integer)i+1) == (integer)x[i];
     //@ assert arr_sum(&x[0], 0, (integer)N) == arr_sum(&x[0], 0, (integer)i) + (integer)x[i] + arr_sum(&x[0], (integer)i+1, (integer)N);
     //@ assert arr_sum(&x[0], 0, (integer)N) == \at(arr_sum(&x[0], 0, (integer)N), L_body) - \at(x[i], L_body) + (integer)x[i];
  }
  //@ assert arr_sum(&x[0], 0, (integer)N) == arr_sum(&x[0], 0, (integer)(N-1)) + (integer)x[N-1];
  //@ assert (integer)x[N-1] == \at((integer)x[N-1], L_rot);
  //@ assert arr_sum(&x[0], 0, (integer)(N-1)) == \at(arr_sum(&x[0], 0, (integer)N), L_rot) - (integer)temp;
  x[N-1] = temp;
  //@ assert arr_sum(&x[0], 0, (integer)(N-1)) == \at(arr_sum(&x[0], 0, (integer)N), L_rot) - (integer)temp;
  //@ assert arr_sum(&x[0], 0, (integer)N) == arr_sum(&x[0], 0, (integer)(N-1)) + (integer)temp;
  //@ assert arr_sum(&x[0], 0, (integer)N) == \at(arr_sum(&x[0], 0, (integer)N), L_rot);
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
