#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100000
#define fun xor
#include <assert.h>
/*@
  logic integer xor_fold(int *a, integer lo, integer hi) =
    lo >= hi ? 0 : (a[lo] ^ xor_fold(a, lo + 1, hi));
*/
/*@
  requires N > 0;
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures \result == xor_fold(&x[0], 0, N);
*/
int xor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= N;
    loop invariant res == xor_fold(&x[0], 0, i);
    loop assigns i, res;
    loop variant N - i;
  */
  for (i = 1; i < N; i++) {
    res = res ^ x[i];
  }
  return res;
}
/*@
  assigns \nothing;
  ensures \result == 1;
*/
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
  //@ assert ret == xor_fold(&x[0], 0, N);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  //@ assert ret2 == xor_fold(&x[0], 0, N);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \old(x[j+1]);
    loop invariant \forall integer j; i+1 <= j < N ==> x[j] == \old(x[j]);
    loop assigns i, x[0 .. N-1];
    loop variant N-1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert ret5 == xor_fold(&x[0], 0, N);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
