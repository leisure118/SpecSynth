#include<limits.h>
/*@
assigns \nothing;
ensures 0 < \result < 10000;
*/
int unknown1();
/*@
assigns \nothing;
ensures INT_MIN <= \result < 100000;
*/
int unknown2();
int main()
{
  int i;
  int j=unknown1();
  int n=unknown2();
  //@ assert(n < 100000);
  int a[n];
  //@ assert(j>0 && j < 10000);
  for(i=1;i<n;i++) {
    int k=unknown1();
    //@ assert(k>0 && k < 10000);
    a[i]=i+j+k;
  }
  for(i=1;i<n;i++){
    //@ assert(a[i]>=(i+2));
  }
  return 0;
}  
