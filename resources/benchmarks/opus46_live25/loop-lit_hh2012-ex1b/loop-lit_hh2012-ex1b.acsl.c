#include <assert.h>
int main() {
  int i = 0;
  /*@
    loop invariant 0 <= i <= 100;
    loop assigns i;
    loop variant 100 - i;
  */
  while (i < 100) {
    int j = 0;
    /*@
      loop invariant 0 <= j <= 100;
      loop assigns j;
      loop variant 100 - j;
    */
    while (j < 100) {
      j++;
      //@ assert(j <= 100);
    }
    //@ assert(j == 100);
    i++;
    //@ assert(i <= 100);
  }
  //@ assert(i == 100);
  return 0;
}
