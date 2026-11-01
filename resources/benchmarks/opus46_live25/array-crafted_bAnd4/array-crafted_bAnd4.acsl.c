#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown(void);
#define N 100000
#define fun bAnd
#include <assert.h>

/*@ axiomatic BandFold {
    logic integer band_fold{L}(int *x, integer n) reads x[0 .. n-1];

    axiom band_one{L}: \forall int *x;
      band_fold{L}(x, 1) == (integer)x[0];

    axiom band_rec{L}: \forall int *x, integer n;
      n >= 2 ==> band_fold{L}(x, n) == (band_fold{L}(x, n-1) & (integer)x[n-1]);

    axiom band_swap_01{L1, L2}: \forall int *x, integer n;
      n >= 2 ==>
      \at(x[0], L2) == \at(x[1], L1) ==>
      \at(x[1], L2) == \at(x[0], L1) ==>
      (\forall integer i; 2 <= i < n ==> \at(x[i], L2) == \at(x[i], L1)) ==>
      band_fold{L2}(x, n) == band_fold{L1}(x, n);

    axiom band_lrot{L1, L2}: \forall int *x, integer n;
      n >= 2 ==>
      (\forall integer i; 0 <= i < n-1 ==> \at(x[i], L2) == \at(x[i+1], L1)) ==>
      \at(x[n-1], L2) == \at(x[0], L1) ==>
      band_fold{L2}(x, n) == band_fold{L1}(x, n);

    axiom band_range{L}: \forall int *x, integer n;
      n >= 1 ==> INT_MIN <= band_fold{L}(x, n) <= INT_MAX;
  }
*/

/*@
  requires \valid_read(x+(0..99999));
  assigns \nothing;
  ensures \result == band_fold(x, 100000);
*/
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= 100000;
    loop invariant res == band_fold(x, i);
    loop assigns i, res;
    loop variant 100000 - i;
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
    loop invariant 0 <= i <= 100000;
    loop assigns i, x[0 .. 99999];
    loop variant 100000 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  BeforeSwap: ;
  temp=x[0];x[0] = x[1]; x[1] = temp;
  AfterSwap: ;
  //@ assert \at(x[0], AfterSwap) == \at(x[1], BeforeSwap);
  //@ assert \at(x[1], AfterSwap) == \at(x[0], BeforeSwap);
  //@ assert \forall integer i; 2 <= i < 100000 ==> \at(x[i], AfterSwap) == \at(x[i], BeforeSwap);
  //@ assert band_fold{AfterSwap}(&x[0], 100000) == band_fold{BeforeSwap}(&x[0], 100000);
  //@ assert ret == band_fold{BeforeSwap}(&x[0], 100000);
  ret2 = fun(x);
  //@ assert ret2 == band_fold{AfterSwap}(&x[0], 100000);
  //@ assert ret == ret2;
  BeforeRot: ;
  temp=x[0];
  /*@
    loop invariant 0 <= i <= 99999;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], BeforeRot);
    loop invariant \forall integer j; i <= j < 100000 ==> x[j] == \at(x[j], BeforeRot);
    loop invariant temp == \at(x[0], BeforeRot);
    loop assigns i, x[0 .. 99998];
    loop variant 99999-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  AfterRot: ;
  //@ assert \forall integer i; 0 <= i < 99999 ==> \at(x[i], AfterRot) == \at(x[i+1], BeforeRot);
  //@ assert \at(x[99999], AfterRot) == \at(x[0], BeforeRot);
  //@ assert band_fold{AfterRot}(&x[0], 100000) == band_fold{BeforeRot}(&x[0], 100000);
  //@ assert ret2 == band_fold{BeforeRot}(&x[0], 100000);
  ret5 = fun(x);
  //@ assert ret5 == band_fold{AfterRot}(&x[0], 100000);
  //@ assert ret2 == ret5;
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
