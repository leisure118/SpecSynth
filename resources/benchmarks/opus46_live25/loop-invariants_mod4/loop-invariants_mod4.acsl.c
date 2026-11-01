#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(void) {
  unsigned int x = 0;
  /*@
    loop invariant x % 4 == 0;
    loop invariant x <= 4294967292;
    loop assigns x;
  */
  while (unknown()) {
    //@ assert x + 4 <= 4294967295 || x + 4 == 4294967296;
    //@ assert x + 4 <= 4294967295 ==> (unsigned int)(x + 4) == x + 4;
    //@ assert x + 4 == 4294967296 ==> (unsigned int)(x + 4) == 0;
    x += 4;
  }
  //@ assert(!(x % 4));
  return 0;
}
