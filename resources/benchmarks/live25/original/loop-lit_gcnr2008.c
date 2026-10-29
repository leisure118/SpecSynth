#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    int x,y,z,w;
    x = y = z = w = 0;
    while (unknown() && y < 10000) {
	if (unknown()) {
	    x = x + 1;
	    y = y + 100;
	} else if (unknown()) {
	    if (x >= 4) {
		x = x + 1;
		y = y + 1;
	    }
	} else if (y > 10*w && z >= 100*x) {
	    y = -y;
	}
	w = w + 1;
	z = z + 10;
    }
    //@ assert(x >= 4 && y <= 2);
    return 0;
}
