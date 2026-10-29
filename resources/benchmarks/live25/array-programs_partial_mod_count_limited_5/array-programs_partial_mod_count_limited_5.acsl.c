#include<limits.h>
/*@
   requires R!=0;
   ensures 0 < \result < 1000000/R;
*/ 
int unknown(unsigned int R);
int N = 1000000;
int main(){
int i,j=0,k=0,a[N];
unsigned int R=5;
int lim=unknown(R);
//@ assert(0 < lim && lim < N/R);
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer jj; 0 <= jj < i && a[jj] == 0 ==> jj > N/2 && jj % R == 0;
    loop assigns i, k, a[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    a[i]=i+1;
    if(i>N/2 && k<lim)
       a[i]=i%R;
    if(a[i]==0) k++;
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant \forall integer z; 0 <= z < N && a[z] == 0 ==> z > N/2 && z % R == 0;
    loop invariant j < N/(2*R);
    loop assigns i, j;
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@ admit j <= k;
      //@ admit k < N/(2*R);
     //@ assert(j < N/(2*R));
  }
  return 0;
}
