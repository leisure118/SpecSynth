#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int i = unknown();
  int k = unknown();
  int n = unknown();
  if (!(i==0 && k==n && n>=0)) return 0;
  while (i<n) {
    k--;
    i+=2;
  }
  //@ assert(2*k>=n-1);
  return 0;
}
