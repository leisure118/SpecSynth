#include <limits.h>
/*@
ensures INT_MIN <= \result <= INT_MAX;
*/
int unknown_int();
int main() {
	int n;
	int k = 0;
	int i = 0;
	n = unknown_int();

	/*@
	  loop invariant 0 <= i;
	  loop invariant k == i;
	  loop invariant i <= n || n <= 0;
	  loop assigns i, k;
	  loop variant n - i;
	*/
	while (i < n) {
		i++;
		k++;
	}
	int j = n;
	/*@
	  loop invariant k >= j;
	  loop invariant j <= n;
	  loop assigns j, k;
	  loop variant j;
	*/
	while (j > 0) {
		//@ assert(k > 0);
		j--;
		k--;
	}

	return 0;
}