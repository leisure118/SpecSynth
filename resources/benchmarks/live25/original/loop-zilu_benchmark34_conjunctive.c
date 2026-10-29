#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int j = unknown();
  int k = unknown();
  int n = unknown();
  if (!((j==0) && (k==n) && (n>0))) return 0;
  while (j<n && n>0) {
    j++;k--;
  }
  //@ assert((k == 0));
  return 0;
}
