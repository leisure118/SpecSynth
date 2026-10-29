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
  for(i=0;i<N;i++){
    a[i]=i+1;
    if(i>N/R && k<lim)
       a[i]=i%R;
    if(a[i]==0) k++;
  }
  for(i=0;i<N;i++){
    if (a[i]==0) j++;
     //@ assert(j <= ((N*(R-1))/(R*R)));
  }
  return 0;
}
