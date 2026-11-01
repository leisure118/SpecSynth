#include "assert.h"
int main() {
    int i,j,k;
    i = 0;
    k = 9;
    j = -100;
    /*@
      loop invariant 0 <= i <= 101;
      loop invariant (i == 0 && k == 9) || (i >= 1 && k == 4);
      loop assigns i, j, k;
      loop variant 101 - i;
    */
    while (i <= 100) {
	i = i + 1;
	/*@
	  loop invariant i >= 1;
	  loop assigns j;
	  loop variant 20 - j;
	*/
	while (j < 20) {
	    j = i + j;
	}
	k = 4;
	/*@
	  loop invariant k == 4;
	  loop assigns k;
	  loop variant 4 - k;
	*/
	while (k <= 3) {
	    k = k + 1;
	}
    }
    //@ assert(k == 4);
    return 0;
}
