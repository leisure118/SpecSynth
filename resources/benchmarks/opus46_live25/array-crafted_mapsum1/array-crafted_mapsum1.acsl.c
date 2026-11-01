#include<limits.h>

/*@ axiomatic ArraySum {
  logic integer asum(int *x, integer lo, integer hi) reads x[lo .. hi-1];
  axiom asum_empty: \forall int *x, integer lo, hi; hi <= lo ==> asum(x, lo, hi) == 0;
  axiom asum_step: \forall int *x, integer lo, integer hi; lo < hi ==>
    asum(x, lo, hi) == asum(x, lo, hi-1) + x[hi-1];
  axiom asum_left: \forall int *x, integer lo, integer hi; lo < hi ==>
    asum(x, lo, hi) == x[lo] + asum(x, lo+1, hi);
  axiom asum_concat: \forall int *x, integer lo, mid, hi; lo <= mid <= hi ==>
    asum(x, lo, hi) == asum(x, lo, mid) + asum(x, mid, hi);
} */

/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown(void);
#define N 100
#define fun mapsum
#include <assert.h>

/*@
  requires \valid_read(x + (0..99));
  assigns \nothing;
  ensures \result == (int)(4950 + asum(x, 0, 100));
*/
int mapsum (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= 100;
    loop invariant ret == i*(i-1)/2 + asum(x, 0, i);
    loop assigns i, ret;
    loop variant 100 - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret+ i + x[i];
  }
  return ret;
}

/*@
  requires \valid(x + (0..99));
  assigns x[0], x[1];
  ensures x[0] == \old(x[1]);
  ensures x[1] == \old(x[0]);
  ensures \forall integer k; 2 <= k < 100 ==> x[k] == \old(x[k]);
*/
void do_swap(int *x) {
  int t = x[0]; x[0] = x[1]; x[1] = t;
}

/*@
  requires \valid(x + (0..99));
  assigns x[0 .. 98];
  ensures \forall integer j; 0 <= j < 99 ==> x[j] == \old(x[j+1]);
  ensures x[99] == \old(x[99]);
*/
void do_shift(int *x) {
  /*@
    loop invariant 0 <= i <= 99;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], Pre);
    loop invariant \forall integer j; i <= j < 100 ==> x[j] == \at(x[j], Pre);
    loop assigns i, x[0 .. 98];
    loop variant 99 - i;
  */
  for(int i = 0; i < 99; i++){
    x[i] = x[i+1];
  }
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
    loop assigns i, x[0 .. 99];
    loop variant 100 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  do_swap(&x[0]);
  //@ assert asum(&x[0], 0, 2) == x[0] + x[1];
  //@ assert asum(&x[0], 0, 100) == asum(&x[0], 0, 2) + asum(&x[0], 2, 100);
  ret2 = fun(x);
  temp=x[0];
  do_shift(&x[0]);
  //@ assert asum(&x[0], 0, 100) == asum(&x[0], 0, 99) + x[99];
  x[N-1] = temp;
  //@ assert asum(&x[0], 0, 100) == asum(&x[0], 0, 99) + x[99];
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
