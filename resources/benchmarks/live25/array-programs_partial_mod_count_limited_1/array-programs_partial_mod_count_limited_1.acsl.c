#include<limits.h>
/*@
   requires R!=0;
   ensures 0 < \result < 1000000/R;
*/
int unknown(unsigned int R);
int N = 1000000;
int main(){
int i,j=0,k=0,a[N];
unsigned int R=1;
int lim=unknown(R);
//@ assert(0 < lim && lim < N/R);
  /*@
    loop invariant 0 <= i <= N;
    loop invariant 0 <= k <= lim;
    loop invariant i <= lim ==> k == i;
    loop invariant i >= lim ==> k == lim;
    loop invariant \forall integer j; 0 <= j < i && j < lim ==> a[j] == 0;
    loop invariant \forall integer j; lim <= j < i ==> a[j] == j+1;
    loop invariant 0 < lim && lim < N/R;
    loop assigns i, k, a[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    a[i]=i+1;
    if(k<lim)
       a[i]=i%R;
    if(a[i]==0) k++;
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer j; 0 <= j < N && j < lim ==> a[j] == 0;
    loop invariant \forall integer j; lim <= j < N ==> a[j] == j+1;
    loop invariant j <= i;
    loop invariant j <= lim;
    loop invariant 0 < lim && lim < N/R;
    loop assigns i, j;
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@ assert(j < N/R);
  }
  return 0;
}
