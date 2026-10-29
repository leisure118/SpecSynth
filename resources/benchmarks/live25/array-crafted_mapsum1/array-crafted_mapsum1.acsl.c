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
  axiomatic Sum {
    logic integer sum_between{L}(int *a, integer b, integer e);
    axiom sum_between_empty{L}:
      \forall int *a, integer b, e; b >= e ==> sum_between{L}(a, b, e) == 0;
    axiom sum_between_one_step{L}:
      \forall int *a, integer i; 0 <= i ==>
        sum_between{L}(a, 0, i+1) == sum_between{L}(a, 0, i) + a[i];
  }
*/

/*@
  requires \valid(x+(0 .. N-1));
  ensures \result == (int)(sum_between{Here}(x, 0, N) + N*(N-1)/2);
  assigns \nothing;
*/
int mapsum (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant ret == sum_between{Here}(x, 0, i) + i*(i-1)/2;
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
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= N-1;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], LoopEntry);
    loop invariant \forall integer j; i <= j < N ==> x[j] == \at(x[j], LoopEntry);
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
