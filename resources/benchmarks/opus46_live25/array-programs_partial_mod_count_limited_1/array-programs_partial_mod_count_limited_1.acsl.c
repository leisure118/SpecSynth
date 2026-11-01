#include<limits.h>
/*@
   requires R!=0;
   assigns \nothing;
   ensures 0 < \result < 1000000/R;
*/ 
int unknown(unsigned int R);
int N = 1000000;
int main(){
int i,j=0,k=0,a[N];
unsigned int R=1;
int lim=unknown(R);
//@ admit \valid(a+(0 .. N-1));
//@ assert(0 < lim && lim < N/R);
  /*@
    loop invariant 0 <= i <= N;
    loop invariant 0 <= k <= lim;
    loop invariant k <= i;
    loop invariant 0 < lim;
    loop invariant lim < N;
    loop invariant i <= lim ==> k == i;
    loop invariant i > lim ==> k == lim;
    loop invariant \forall integer m; 0 <= m < k ==> a[m] == 0;
    loop invariant \forall integer m; k <= m < i ==> a[m] == m + 1;
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
    loop invariant 0 <= j <= lim;
    loop invariant j <= i;
    loop invariant 0 < lim;
    loop invariant lim < N;
    loop invariant i <= lim ==> j == i;
    loop invariant i > lim ==> j == lim;
    loop invariant \forall integer m; 0 <= m < lim ==> a[m] == 0;
    loop invariant \forall integer m; lim <= m < N ==> a[m] == m + 1;
    loop assigns i, j;
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@ assert(j < N/R);
  }
  return 0;
} 
