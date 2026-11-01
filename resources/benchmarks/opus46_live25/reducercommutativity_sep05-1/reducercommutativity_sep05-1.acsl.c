#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 5
#define fun sep
#include <assert.h>
/*@
  requires \valid(x+(0..4));
  assigns \nothing;
  ensures \result == (x[0]%2==0 ? 1 : -1) + (x[1]%2==0 ? 1 : -1) + (x[2]%2==0 ? 1 : -1) + (x[3]%2==0 ? 1 : -1) + (x[4]%2==0 ? 1 : -1);
*/
int sep (int x[N])
{
  long long ret =0;
  /*@
    loop invariant 0 <= i <= 5;
    loop invariant ret ==
      (0 < i ? (x[0]%2==0 ? 1 : -1) : 0) +
      (1 < i ? (x[1]%2==0 ? 1 : -1) : 0) +
      (2 < i ? (x[2]%2==0 ? 1 : -1) : 0) +
      (3 < i ? (x[3]%2==0 ? 1 : -1) : 0) +
      (4 < i ? (x[4]%2==0 ? 1 : -1) : 0);
    loop assigns i, ret;
    loop variant 5 - i;
  */
  for(int i=0;i<N;i++)
  {
    if(x[i]%2==0)
      ret++;
    else
      ret--;
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
  Shift: ;
  /*@
    loop invariant 0 <= i <= 4;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], Shift);
    loop invariant \forall integer j; i <= j <= 4 ==> x[j] == \at(x[j], Shift);
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
