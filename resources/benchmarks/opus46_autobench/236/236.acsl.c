/*@
	requires n >= 0;
*/
void foo(int n){
	int x = n;
	int y = 0;

	/*@
	  loop invariant x + y == n;
	  loop invariant x >= 0;
	  loop invariant y >= 0;
	  loop assigns x, y;
	  loop variant x;
	*/
	while (x > 0) {
		x--;
		y++;
	}

	//@ assert(y == n);
}
