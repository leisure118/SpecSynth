#include<limits.h>

/*@ axiomatic ArraySum {
    logic integer array_sum{L}(int *a, integer lo, integer hi)
      reads a[lo .. hi-1];

    axiom sum_empty{L}: \forall int *a, integer lo, hi;
      hi <= lo ==> array_sum(a, lo, hi) == 0;

    axiom sum_next{L}: \forall int *a, integer lo, hi;
      lo < hi ==> array_sum(a, lo, hi) == array_sum(a, lo, hi-1) + a[hi-1];

    axiom sum_head{L}: \forall int *a, integer lo, hi;
      lo < hi ==> array_sum(a, lo, hi) == a[lo] + array_sum(a, lo+1, hi);

    axiom sum_rotation{L1,L2}: \forall int *a, integer n;
      n > 0 ==>
      (\forall integer j; 0 <= j < n-1 ==> \at(a[j],L2) == \at(a[j+1],L1)) ==>
      \at(a[n-1],L2) == \at(a[0],L1) ==>
      array_sum{L1}(a, 0, n) == array_sum{L2}(a, 0, n);

    axiom sum_frame{L1,L2}: \forall int *a, integer lo, hi;
      (\forall integer j; lo <= j < hi ==> \at(a[j],L1) == \at(a[j],L2)) ==>
      array_sum{L1}(a, lo, hi) == array_sum{L2}(a, lo, hi);
}*/

/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown(void);
#define N 1000
#define fun mapsum
#include <assert.h>

/*@ logic integer mapsum_math(int *x) =
      (integer)N*((integer)N-1)/2 + array_sum(x, 0, (integer)N); */

/*@
  requires \valid(x+(0 .. N-1));
  assigns \nothing;
  ensures \result == (int)mapsum_math(x);
*/
int mapsum (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant (integer)ret == (integer)i*((integer)i-1)/2 + array_sum(x, 0, (integer)i);
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
  //@ assert array_sum(&x[0], 0, (integer)N) == (integer)x[0] + array_sum(&x[0], 1, (integer)N);
  //@ assert array_sum(&x[0], 1, (integer)N) == (integer)x[1] + array_sum(&x[0], 2, (integer)N);
  Bs: ;
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert \forall integer j; 2 <= j < N ==> (integer)x[j] == \at((integer)x[j], Bs);
  //@ assert array_sum(&x[0], 2, (integer)N) == array_sum{Bs}(&x[0], 2, (integer)N);
  //@ assert array_sum(&x[0], 0, (integer)N) == (integer)x[0] + array_sum(&x[0], 1, (integer)N);
  //@ assert array_sum(&x[0], 1, (integer)N) == (integer)x[1] + array_sum(&x[0], 2, (integer)N);
  //@ assert array_sum(&x[0], 0, (integer)N) == array_sum{Bs}(&x[0], 0, (integer)N);
  ret2 = fun(x);
  temp=x[0];
  Rot: ;
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> (integer)x[j] == \at((integer)x[j+1], Rot);
    loop invariant \forall integer j; i <= j < N ==> (integer)x[j] == \at((integer)x[j], Rot);
    loop assigns i, x[0 .. N-2];
    loop variant N-1-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert \forall integer j; 0 <= j < N-1 ==> (integer)x[j] == \at((integer)x[j+1], Rot);
  //@ assert (integer)x[N-1] == \at((integer)x[0], Rot);
  //@ assert array_sum(&x[0], 0, (integer)N) == array_sum{Rot}(&x[0], 0, (integer)N);
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
