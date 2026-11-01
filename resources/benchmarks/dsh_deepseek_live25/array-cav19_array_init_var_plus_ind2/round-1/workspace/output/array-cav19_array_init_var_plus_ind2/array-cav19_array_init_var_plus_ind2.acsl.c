#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int N = 100000;
int main()
{
  int i;
  int j=0;
  int k=0;
  int a[N];
  int x=unknown();
  /*@
  loop invariant 0 <= i <= N;
  loop invariant j == i*(i-1)/2;
  loop invariant -(i*(i-1)/2) <= k <= 0;
  loop invariant \forall integer m; 0 <= m < i ==> a[m] == m*(m-1)/2;
  loop assigns i, x, j, k, a[0 .. N-1];
  loop variant N - i;
  */
  for(i=0;i<N;i++){
    x=unknown();
    if(x) break;
    a[i]=j;
    j=j+i;
    k=k-i;
  }
  /*@
  loop invariant 1 <= l <= i;
  loop invariant \forall integer m; 1 <= m < i ==> a[m] == m*(m-1)/2;
  loop invariant k <= 0;
  loop assigns l;
  loop variant i - l;
  */
  for(int l=1;l<i;l++){
    //@ assert(a[l]>=k);
  }
  return 0;
}
