#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    int x = 0;
    int m = 0;
    int n = unknown();
    while(x < n) {
	if(unknown()) {
	    m = x;
	}
	x = x + 1;
    }
    //@assert((m >= 0 || n <= 0));
    //@assert((m < n || n <= 0));
    return 0;
}
