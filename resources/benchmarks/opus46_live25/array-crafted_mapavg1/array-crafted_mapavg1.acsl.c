#include<limits.h>

/*@ axiomatic Sum {
  logic integer sum(int *a, integer lo, integer hi) reads a[lo .. hi-1];

  axiom sum_empty: \forall int *a, integer lo, hi;
    lo >= hi ==> sum(a, lo, hi) == 0;

  axiom sum_one: \forall int *a, integer i;
    sum(a, i, i+1) == a[i];

  axiom sum_left: \forall int *a, integer lo, hi;
    lo < hi ==> sum(a, lo, hi) == a[lo] + sum(a, lo+1, hi);

  axiom sum_right: \forall int *a, integer lo, hi;
    lo < hi ==> sum(a, lo, hi) == sum(a, lo, hi-1) + a[hi-1];

  axiom sum_split: \forall int *a, integer lo, mid, hi;
    lo <= mid <= hi ==> sum(a, lo, hi) == sum(a, lo, mid) + sum(a, mid, hi);

  axiom sum_elt: \forall int *a, integer lo, hi, k;
    lo <= k < hi ==> sum(a, lo, hi) == sum(a, lo, k) + a[k] + sum(a, k+1, hi);

  axiom sum_bound: \forall int *a, integer lo, hi;
    (\forall integer j; lo <= j < hi ==> -20000000 <= a[j] <= 20000000) ==>
    -20000000*(hi-lo) <= sum(a, lo, hi) <= 20000000*(hi-lo);

  axiom sum_ext: \forall int *a, int *b, integer lo, hi;
    (\forall integer j; lo <= j < hi ==> a[j] == b[j]) ==>
    sum(a, lo, hi) == sum(b, lo, hi);
} */

/*@
assigns \nothing;
ensures -20000000 <= \result <= 20000000;
*/
int unknown(void);
#define N 100
#define fun mapavg
#include <assert.h>

/*@
  requires \valid(x+(0..99));
  requires \forall integer j; 0 <= j < 100 ==> -20000000 <= x[j] <= 20000000;
  assigns \nothing;
  ensures \result == (4950 + sum(x, 0, 100)) / 100;
*/
int mapavg (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= 100;
    loop invariant ret == i*(i-1)/2 + sum(x, 0, i);
    loop assigns i, ret;
    loop variant 100 - i;
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
    loop invariant 0 <= i <= 100;
    loop invariant \forall integer j; 0 <= j < i ==> -20000000 <= x[j] <= 20000000;
    loop assigns i, x[0 .. 99];
    loop variant 100 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  L1: ;
  //@ assert sum(&x[0], 0, 100) == x[0] + x[1] + sum(&x[0], 2, 100);
  //@ assert \separated(&x[0] + (0 .. 1), &x[0] + (2 .. 99));
  temp=x[0];
  x[0] = x[1];
  x[1] = temp;
  //@ assert x[0] + x[1] == \at(x[0], L1) + \at(x[1], L1);
  //@ assert \forall integer j; 2 <= j < 100 ==> x[j] == \at(x[j], L1);
  //@ assert sum(&x[0], 0, 100) == x[0] + x[1] + sum(&x[0], 2, 100);
  //@ assert sum(&x[0], 0, 100) == \at(sum(&x[0], 0, 100), L1);
  //@ assert \forall integer j; 0 <= j < 100 ==> -20000000 <= x[j] <= 20000000;
  ret2 = fun(x);
  L2: ;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= 99;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], L2);
    loop invariant \forall integer j; i <= j < 100 ==> x[j] == \at(x[j], L2);
    loop invariant \forall integer j; 0 <= j < 100 ==> -20000000 <= x[j] <= 20000000;
    loop assigns i, x[0 .. 98];
    loop variant 99-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert \forall integer j; 0 <= j < 99 ==> x[j] == \at(x[j+1], L2);
  //@ assert x[99] == \at(x[0], L2);
  //@ assert \forall integer j; 0 <= j < 100 ==> x[j] == \at(x[(j+1) % 100], L2);
  //@ assert sum(&x[0], 0, 100) == \at(sum(&x[0], 0, 100), L2);
  //@ assert \forall integer j; 0 <= j < 100 ==> -20000000 <= x[j] <= 20000000;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
