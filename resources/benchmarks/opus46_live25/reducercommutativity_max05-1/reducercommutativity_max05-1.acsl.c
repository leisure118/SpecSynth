#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 5
#define fun max
#include <assert.h>
/*@
  requires \valid(x+(0..4));
  assigns \nothing;
  ensures \result >= 0;
  ensures \forall integer k; 0 <= k < 5 ==> \result >= x[k];
  ensures \result == 0 || \result == x[0] || \result == x[1] || \result == x[2] || \result == x[3] || \result == x[4];
*/
int max (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@
    loop invariant 0 <= i <= 5;
    loop invariant ret >= 0;
    loop invariant \forall integer j; 0 <= j < i ==> ret >= x[j];
    loop invariant ret == 0 || (i >= 1 && ret == x[0]) || (i >= 2 && ret == x[1]) || (i >= 3 && ret == x[2]) || (i >= 4 && ret == x[3]) || (i >= 5 && ret == x[4]);
    loop assigns i, ret;
    loop variant 5 - i;
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
    loop invariant 0 <= i <= 5;
    loop assigns i, x[0 .. 4];
    loop variant 5 - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  //@ assert ret >= x[0] && ret >= x[1] && ret >= x[2] && ret >= x[3] && ret >= x[4];
  //@ assert ret == 0 || ret == x[0] || ret == x[1] || ret == x[2] || ret == x[3] || ret == x[4];
  ret2 = fun(x);
  temp=x[0];
  /*@
    loop invariant 0 <= i <= 4;
    loop invariant i == 0 ==> x[0] == temp;
    loop invariant i >= 1 ==> x[i-1] == x[i];
    loop invariant \forall integer j; 0 <= j < 5 ==> ret >= x[j];
    loop invariant \forall integer j; 0 <= j < 5 ==> ret2 >= x[j];
    loop invariant ret >= 0;
    loop invariant ret2 >= 0;
    loop invariant ret >= temp;
    loop invariant ret2 >= temp;
    loop invariant ret == 0 || ret == temp || ret == x[0] || ret == x[1] || ret == x[2] || ret == x[3] || ret == x[4];
    loop invariant ret2 == 0 || ret2 == temp || ret2 == x[0] || ret2 == x[1] || ret2 == x[2] || ret2 == x[3] || ret2 == x[4];
    loop assigns i, x[0 .. 3];
    loop variant 4-i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  //@ assert ret >= x[0] && ret >= x[1] && ret >= x[2] && ret >= x[3] && ret >= x[4];
  //@ assert ret == 0 || ret == x[0] || ret == x[1] || ret == x[2] || ret == x[3] || ret == x[4];
  //@ assert ret2 >= x[0] && ret2 >= x[1] && ret2 >= x[2] && ret2 >= x[3] && ret2 >= x[4];
  //@ assert ret2 == 0 || ret2 == x[0] || ret2 == x[1] || ret2 == x[2] || ret2 == x[3] || ret2 == x[4];
  ret5 = fun(x);
  //@ assert ret5 >= x[0] && ret5 >= x[1] && ret5 >= x[2] && ret5 >= x[3] && ret5 >= x[4];
  //@ assert ret5 == 0 || ret5 == x[0] || ret5 == x[1] || ret5 == x[2] || ret5 == x[3] || ret5 == x[4];
  //@ assert ret >= ret5;
  //@ assert ret5 >= ret;
  //@ assert ret == ret2;
  //@ assert ret == ret5;
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
