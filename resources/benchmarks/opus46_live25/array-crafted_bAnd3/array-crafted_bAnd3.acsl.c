#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown(void);
#define N 10000
#define fun bAnd
#include <assert.h>

/*@ logic integer band_all(int *a, integer n) =
      n <= 1 ? a[0] : (band_all(a, n-1) & a[n-1]);
*/

/*@ axiomatic BandAllProps {
  axiom band_all_swap_01{L1, L2}: \forall int *a, integer n;
    n >= 2 ==>
    \at(a[0], L2) == \at(a[1], L1) ==>
    \at(a[1], L2) == \at(a[0], L1) ==>
    (\forall integer k; 2 <= k < n ==> \at(a[k], L2) == \at(a[k], L1)) ==>
    band_all{L2}(a, n) == band_all{L1}(a, n);

  axiom band_all_rotate_left{L1, L2}: \forall int *a, integer n;
    n >= 2 ==>
    (\forall integer k; 0 <= k < n-1 ==> \at(a[k], L2) == \at(a[k+1], L1)) ==>
    \at(a[n-1], L2) == \at(a[0], L1) ==>
    band_all{L2}(a, n) == band_all{L1}(a, n);
}
*/

/*@
  requires \valid(x+(0..9999));
  assigns \nothing;
  ensures \result == (int)band_all(x, 10000);
*/
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= 10000;
    loop invariant (integer)res == band_all(x, i);
    loop assigns i, res;
    loop variant 10000 - i;
  */
  for (i = 1; i < N; i++) {
    res = res & x[i];
  }
  return res;
}

int main ()
{
  int x[N];
  int temp;
  int ret;
  int ret2;
  int ret5;
  /*@
    loop invariant 0 <= i <= 10000;
    loop assigns i, x[0 .. 9999];
    loop variant 10000 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  L1:
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  L2:
  ret2 = fun(x);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= 9999;
    loop invariant \forall integer k; 0 <= k < i ==> x[k] == \at(x[k+1], L2);
    loop invariant \forall integer k; i <= k < 10000 ==> x[k] == \at(x[k], L2);
    loop invariant (integer)temp == (integer)\at(x[0], L2);
    loop assigns i, x[0 .. 9998];
    loop variant 9999-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  L3:
  ret5 = fun(x);
  //@ assert \at(x[0], L2) == \at(x[1], L1);
  //@ assert \at(x[1], L2) == \at(x[0], L1);
  //@ assert \forall integer k; 2 <= k < 10000 ==> \at(x[k], L2) == \at(x[k], L1);
  //@ assert band_all{L2}(&x[0], 10000) == band_all{L1}(&x[0], 10000);
  //@ assert band_all{L3}(&x[0], 10000) == band_all{L2}(&x[0], 10000);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
