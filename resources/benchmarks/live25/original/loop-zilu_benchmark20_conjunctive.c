#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int i = unknown();
  int n = unknown();
  int sum = unknown();
  if (!(i==0 && n>=0 && n<=100 && sum==0)) return 0;
  while (i<n) {
    sum = sum + i;
    i++;
  }
  //@ assert(sum>=0);
  return 0;
}
