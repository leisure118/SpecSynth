#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown(void);
#define N 10000
#define fun mapsum
#include <assert.h>

/*@ axiomatic ArraySum {
  logic integer array_sum(int *a, integer lo, integer hi) reads a[lo .. hi-1];

  axiom sum_empty: \forall int *a, integer lo, hi;
    lo >= hi ==> array_sum(a, lo, hi) == 0;

  axiom sum_append: \forall int *a, integer lo, hi;
    lo < hi ==> array_sum(a, lo, hi) == array_sum(a, lo, hi-1) + a[hi-1];

  axiom sum_prepend: \forall int *a, integer lo, hi;
    lo < hi ==> array_sum(a, lo, hi) == a[lo] + array_sum(a, lo+1, hi);

  axiom sum_one: \forall int *a, integer i;
    array_sum(a, i, i+1) == a[i];

  axiom sum_split: \forall int *a, integer lo, mid, hi;
    lo <= mid <= hi ==> array_sum(a, lo, hi) == array_sum(a, lo, mid) + array_sum(a, mid, hi);
}*/

/*@
  requires \valid(x+(0 .. N-1));
  assigns \nothing;
  ensures \result == (int)((integer)(N-1)*N/2 + array_sum(x, 0, N));
*/
int mapsum (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant ret == (integer)i*(i-1)/2 + array_sum(x, 0, i);
    loop assigns i, ret;
    loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret+ i + x[i];
  }
  return ret;
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
  L_swap: ;
  /*@ assert array_sum(&x[0], 0, N) == (integer)x[0] + (integer)x[1] + array_sum(&x[0], 2, N); */
  temp=x[0];x[0] = x[1]; x[1] = temp;
  /*@ assert array_sum(&x[0], 0, N) == (integer)x[0] + (integer)x[1] + array_sum(&x[0], 2, N); */
  /*@ assert (integer)x[0] + (integer)x[1] == (integer)\at(x[0], L_swap) + (integer)\at(x[1], L_swap); */
  /*@ assert array_sum(&x[0], 2, N) == \at(array_sum(&x[0], 2, N), L_swap); */
  /*@ assert array_sum(&x[0], 0, N) == \at(array_sum(&x[0], 0, N), L_swap); */
  ret2 = fun(x);
  L_rot: ;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], L_rot);
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], L_rot);
    loop assigns i, x[0 .. N-2];
    loop variant N-1-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  /*@ assert \forall integer j; 0 <= j < N-1 ==> x[j] == \at(x[j+1], L_rot); */
  /*@ assert x[N-1] == \at(x[0], L_rot); */
  /*@ assert array_sum(&x[0], 0, N) == \at(array_sum(&x[0], 0, N), L_rot); */
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
