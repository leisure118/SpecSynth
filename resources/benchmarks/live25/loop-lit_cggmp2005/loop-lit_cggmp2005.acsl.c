#include "assert.h"
int main() {
    int i,j;
    i = 1;
    j = 10;
    /*@
      loop invariant i + 2*j == 21;
      loop invariant 6 <= j;
      loop assigns i, j;
      loop variant j - i;
    */
    while (j >= i) {
        i = i + 2;
        j = -1 + j;
    }
    //@ assert(j == 6);
    return 0;
}
