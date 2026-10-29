#include<limits.h>
#include<limits.h>
/*@
assigns \nothing;
ensures 1 < \result < 6;
*/
unsigned int unknown1();
/*@
    requires R!=0;
    ensures 0 < \result < 1000/R;
*/
int unknown2(unsigned int R);
int N = 1000;
int main(){
int i,j=0,k=0,a[N];
unsigned int R=unknown1();
int lim=unknown2(R);
 //@ assert(R>1 && R<6);
//@ assert(0 < lim && lim < N/R);
  //@ admit \valid(a+(0 .. N-1));
  /*@
    loop invariant 0 <= i <= N;
    loop invariant k <= lim;
    loop invariant \forall integer j; 0 <= j < i && j <= N/R ==> a[j] == j+1;
    loop invariant \forall integer j; 0 <= j < i && a[j] == 0 ==> j > N/R && j % R == 0;
    loop assigns i, k, a[0 .. N-1];
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    a[i]=i+1;
    if(i>N/R && k<lim)
       a[i]=i%R;
    if(a[i]==0) k++;
  }
  /*@
    loop invariant 0 <= i <= N;
    loop invariant j <= ((N*(R-1))/(R*R));
    loop invariant \forall integer jj; 0 <= jj < N && a[jj] == 0 ==> jj > N/R && jj % R == 0;
    loop assigns i, j;
    loop variant N - i;
  */
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@ assert(j <= ((N*(R-1))/(R*R)));
  }
  return 0;
}
