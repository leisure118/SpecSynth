/*@
	requires n >= 0;
*/
void foo(int n){
	int x = n;
	int y = 0;

	/*@
	  loop invariant 0 <= x <= n;
	  loop invariant y == n - x;
	  loop assigns x, y;
	  loop variant x;
	*/
	while (x > 0) {
		x--;
		y++;
	}

	//@ assert(y == n);
}
