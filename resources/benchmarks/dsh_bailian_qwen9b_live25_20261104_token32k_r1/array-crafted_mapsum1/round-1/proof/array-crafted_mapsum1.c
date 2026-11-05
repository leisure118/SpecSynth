#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100
#define fun mapsum
#include <assert.h>
/*@
  logic integer mapsum_spec(int *x, integer n) =
    n <= 0 ? 0 : mapsum_spec(x, n-1) + (n-1) + x[n-1];
*/
/*@
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures \result == mapsum_spec(x, N);
*/
int mapsum (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@ loop invariant 0 <= i <= N;
      loop invariant ret == mapsum_spec(x, i);
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
  /*@ loop invariant 0 <= i <= N;
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
  /*@ loop invariant 0 <= i <= N-1;
      loop assigns i, x[0 .. N-2];
      loop variant (N-1) - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
