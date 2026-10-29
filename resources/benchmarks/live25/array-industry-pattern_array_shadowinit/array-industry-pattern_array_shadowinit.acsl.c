#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
#define fun main
int N;
int main() {
 N=unknown();
 if(N>0) {
  int i,k;
  int a[N];
  i=0;
  k=0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant 0 <= k <= N;
    loop invariant i == k;
    loop invariant \forall integer j; 0 <= j < i ==> a[j] == j;
    loop assigns i, k, a[0 .. N-1];
    loop variant N - i;
  */
  while(i < N) {
   a[k]=k;
   i=i+1;
   k=k+1;
  }
  i=0;
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < N ==> a[j] == j;
    loop assigns i;
    loop variant N - i;
  */
  while(i < N) {
   //@ assert(a[i]==i);
   i=i+1;
  }
 }
 return 0;
}
