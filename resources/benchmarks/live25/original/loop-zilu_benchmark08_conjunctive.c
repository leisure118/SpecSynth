#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int n = unknown();
  int sum = unknown();
  int i = unknown();
  if (!(n>=0 && sum==0 && i==0)) return 0;
  while (i<n) {
    sum=sum+i;
    i++;
  }
  //@ assert(sum>=0);
  return 0;
}
