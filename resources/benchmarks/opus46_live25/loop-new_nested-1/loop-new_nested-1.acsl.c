#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#include "assert.h"
int main() {
    int n = unknown();
    int m = unknown();
    int k = 0;
    int i,j;
    if (!(10 <= n && n <= 10000)) return 0;
    if (!(10 <= m && m <= 10000)) return 0;
    /*@
      loop invariant 0 <= i <= n;
      loop invariant k == i * m;
      loop invariant 10 <= n <= 10000;
      loop invariant 10 <= m <= 10000;
      loop assigns i, j, k;
      loop variant n - i;
    */
    for (i = 0; i < n; i++) {
	/*@
	  loop invariant 0 <= j <= m;
	  loop invariant k == i * m + j;
	  loop assigns j, k;
	  loop variant m - j;
	*/
	for (j = 0; j < m; j++) {
	    k ++;
	}
    }
    //@ assert(k >= 100);
    return 0;
}
