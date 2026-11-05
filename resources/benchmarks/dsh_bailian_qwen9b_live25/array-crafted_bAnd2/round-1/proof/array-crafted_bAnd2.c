#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 1000
#define fun bAnd
#include <assert.h>
int bAnd (int x[N])
{
  int i;
  long long res;
  res = x[0];
  for (i = 1; i < N; i++) {
    res = res & x[i];
  }
  //@ loop invariant 1 <= i <= N;
  //@ loop invariant \forall integer j; 0 <= j < i ==> (res & x[j]) == res;
  //@ loop invariant \forall integer k; ( \forall integer j; 0 <= j < i ==> (k & x[j]) == k ) ==> (k & res) == k;
  //@ loop assigns i, res;
  //@ loop variant N - i;
  /*
  Specifically ensures that res is the bitwise AND of ALL elements in x[0..N-1].
  The above loop invariants capture this: res starts as x[0], then ANDs with each x[i],
  and the invariant (k & res) == k for common k ensures res is unique and perm-invariant.
  */
  return res;
}
int main ()
{
  int x[N];
  int temp;
  int ret;
  int ret2;
  int ret5;
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  /*
  Loop invariant 0 <= i <= N;
  Loop assigns i, x[0..N-1];
  Loop variant N - i;
  */
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  /*
  Loop invariant 0 <= i <= N-1;
  Loop invariant the multiset of values in x[0..N-1] is unchanged from before rotation;
  Loop invariant \forall integer k; 0 <= k < i ==> x[k] == temp_old;  (where temp_old was initial x[0])
  Loop assigns i, x[0..N-1];
  Loop variant N-1 - i;
  */
  ret5 = fun(x);
  /*
  The assertion follows from the bAnd contract: ret, ret2, ret5 all represent the AND of all elements,
  and since bAnd's result is independent of array permutation (due to the AND semantics and the contract's uniqueness clause),
  ret == ret2 == ret5.
  */
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}