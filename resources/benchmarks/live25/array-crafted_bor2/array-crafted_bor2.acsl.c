#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 1000
#define fun bor
#include <assert.h>
/*@
  axiomatic OrFold {
    logic int or_fold{L}(int *a, integer n);
    axiom or_fold_empty{L}: \forall int *a, integer n; n <= 0 ==> or_fold(a, n) == 0;
    axiom or_fold_step{L}: \forall int *a, integer n; n > 0 ==> or_fold(a, n) == (or_fold(a, n-1) | a[n-1]);
    axiom or_fold_1{L}: \forall int *a; or_fold(a, 1) == a[0];
    axiom or_fold_succ{L}: \forall int *a, integer i; 0 < i < 1000 ==> or_fold(a, i+1) == (or_fold(a, i) | a[i]);
  }
*/
/*@
  assigns \nothing;
  ensures \result == or_fold(x, N);
*/
int bor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant res == or_fold(x, i);
    loop assigns i, res;
    loop variant N - i;
  */
  for (i = 1; i < N; i++) {
    res = res | x[i];
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
    loop invariant 0 <= i <= N;
    loop assigns i, x[0 .. N-1];
    loop variant N - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop assigns i, x[0 .. N-2];
    loop variant N-1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
