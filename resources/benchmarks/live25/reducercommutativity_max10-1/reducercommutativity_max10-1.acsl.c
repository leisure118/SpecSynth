#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 10
#define fun max
#include <assert.h>
/*@
  requires \valid(x+(0..9));
  assigns \nothing;
  ensures \result >= 0;
  ensures \forall integer j; 0 <= j < 10 ==> \result >= x[j];
  ensures \result == 0 || \exists integer j; 0 <= j < 10 && \result == x[j];
*/
int max (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= 10;
    loop invariant 0 <= ret <= 2147483647;
    loop invariant \forall integer j; 0 <= j < i ==> ret >= x[j];
    loop invariant ret == 0 || \exists integer j; 0 <= j < i && ret == x[j];
    loop assigns i, ret;
    loop variant 10 - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret < x[i] ? x[i] : ret;
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
    loop invariant 0 <= i <= 10;
    loop assigns i, x[0 .. 9];
    loop variant 10 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  //@ assert \forall integer j; 0 <= j < 10 ==> ret >= x[j];
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert \forall integer j; 0 <= j < 10 ==> ret >= x[j];
  //@ assert ret != 0 ==> \exists integer j; 0 <= j < 10 && ret == x[j];
  ret2 = fun(x);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= 9;
    loop invariant \forall integer j; 0 <= j < i ==> x[j] == \at(x[j+1], LoopEntry);
    loop invariant \forall integer j; i <= j < 9 ==> x[j] == \at(x[j], LoopEntry);
    loop invariant x[9] == \at(x[9], LoopEntry);
    loop invariant temp == \at(x[0], LoopEntry);
    loop assigns i, x[0 .. 8];
    loop variant 9 - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert \forall integer j; 0 <= j < 10 ==> ret >= x[j];
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
