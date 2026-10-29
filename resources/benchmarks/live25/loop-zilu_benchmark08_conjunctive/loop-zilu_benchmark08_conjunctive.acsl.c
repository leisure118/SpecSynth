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
  /*@
    loop invariant 0 <= i <= n;
    loop invariant sum >= 0;
    loop assigns i, sum;
    loop variant n - i;
  */
  while (i<n) {
    sum=sum+i;
    i++;
  }
  //@ assert(sum>=0);
  return 0;
}
