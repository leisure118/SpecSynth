#include <assert.h>
int main() {
  int v = 1; 
  /*@
    loop invariant 1 <= v <= 52;
    loop invariant v % 2 == 1;
    loop assigns v;
    loop variant 51 - v;
  */
  while (v <= 50) {
    //@ assert(1 <= v);
    v += 2;
    //@ assert(v <= 52);
  }
  //@ assert(51 <= v);
  //@ assert(v <= 52);
  return 0;
}
