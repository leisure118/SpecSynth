#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int i = unknown();
  int j = unknown();
  int k = unknown();
  if (!(i<j && k>i-j)) return 0;
  /*@
    loop invariant i <= j;
    loop invariant k > i - j;
    loop assigns i, k;
    loop variant j - i;
  */
  while (i<j) {
    k=k+1;
    i=i+1;
  }
  //@ assert(k > 0);
  return 0;
}
