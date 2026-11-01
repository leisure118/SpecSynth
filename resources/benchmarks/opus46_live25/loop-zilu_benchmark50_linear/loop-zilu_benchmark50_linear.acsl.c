#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include <assert.h>
int main() {
  int xa = unknown();
  int ya = unknown();
  if (!(xa + ya > 0)) return 0;
  /*@
    loop invariant xa + ya > 0;
    loop assigns xa, ya;
    loop variant xa;
  */
  while (xa > 0) {
    xa--;
    ya++;
  }
  //@ assert(ya >= 0);
  return 0;
}
