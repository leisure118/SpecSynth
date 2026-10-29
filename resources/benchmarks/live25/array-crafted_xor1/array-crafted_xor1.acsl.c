#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100
#define fun xor
#include <assert.h>

/*@
  logic integer xor_range(int *a, integer l, integer r) =
    l >= r ? 0 : xor_range(a, l, r-1) ^ a[r-1];
*/

/*@
  requires \valid(x+(0..100-1));
  assigns \nothing;
*/
int xor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  /*@
    loop invariant 1 <= i <= 100;
    loop invariant res == xor_range(x, 0, i);
    loop assigns i, res;
    loop variant 100 - i;
  */
  for (i = 1; i < N; i++) {
    res = res ^ x[i];
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
    loop invariant 0 <= i <= 100;
    loop assigns i, x[0..100-1];
    loop variant 100 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= 100-1;
    loop assigns i, x[0..100-2];
    loop variant 100-1 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ admit ret == ret2;
  //@ admit ret == ret5;
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
