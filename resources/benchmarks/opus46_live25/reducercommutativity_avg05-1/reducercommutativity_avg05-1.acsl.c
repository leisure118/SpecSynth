#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 5
#define fun avg
#include <assert.h>
/*@
  requires \valid(x+(0..4));
  assigns \nothing;
  ensures \result == (x[0] + x[1] + x[2] + x[3] + x[4]) / 5;
*/
int avg (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= 5;
    loop invariant i == 0 ==> ret == 0;
    loop invariant i == 1 ==> ret == x[0];
    loop invariant i == 2 ==> ret == x[0] + x[1];
    loop invariant i == 3 ==> ret == x[0] + x[1] + x[2];
    loop invariant i == 4 ==> ret == x[0] + x[1] + x[2] + x[3];
    loop invariant i == 5 ==> ret == x[0] + x[1] + x[2] + x[3] + x[4];
    loop assigns i, ret;
    loop variant 5 - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret + x[i];
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
    loop invariant 0 <= i <= 5;
    loop assigns i, x[0 .. 4];
    loop variant 5 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  L1: ;
  /*@
    loop invariant 0 <= i <= 4;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], L1);
    loop invariant \forall integer j; i <= j < 5 ==> x[j] == \at(x[j], L1);
    loop assigns i, x[0 .. 3];
    loop variant 4 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
