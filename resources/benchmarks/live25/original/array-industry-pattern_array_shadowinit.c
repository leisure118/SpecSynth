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
  while(i < N) {
   a[k]=k;
   i=i+1;
   k=k+1;
  }
  i=0;
  while(i < N) {
   //@ assert(a[i]==i);
   i=i+1;
  }
 }
 return 0;
}
