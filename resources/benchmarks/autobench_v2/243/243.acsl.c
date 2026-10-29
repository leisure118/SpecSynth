int main() {
    int i;
    int j;

    int x = i;
    int y = j;
    //@ admit i >= 0;
    /*@
      loop invariant (x - y) == (i - j);
      loop invariant x >= 0;
      loop assigns x, y;
      loop variant x;
    */
    while (x != 0) {
    	x--;
    	y--;
    }

    if (i == j) {
    	//@ assert(y == 0);
    }

    return 0;
}
