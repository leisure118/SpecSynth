#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int k = unknown();
  int j = unknown();
  int n = unknown();
  if (!(n>=1 && k>=n && j==0)) return 0;
  while (j<=n-1) {
    j++;
    k--;
  }
  //@ assert(k>=0);
  return 0;
}
