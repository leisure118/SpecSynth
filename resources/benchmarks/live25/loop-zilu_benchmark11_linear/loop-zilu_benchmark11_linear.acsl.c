#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int x = unknown();
  int n = unknown();
  if (!(x==0 && n>0)) return 0;
  /*@
    loop invariant 0 <= x <= n;
    loop assigns x;
    loop variant n - x;
  */
  while (x<n) {
    x++;
  }
  //@ assert(x==n);
  return 0;
}
