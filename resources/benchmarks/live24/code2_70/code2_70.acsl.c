/*@
requires n > 0;
*/
void foo(int n) {
    int x = 1;
    int y = 0;
    /*@
      loop invariant 1 <= x <= n+1;
      loop invariant (x == 1 && y == 0) || (y == n - x + 1);
      loop assigns x, y;
      loop variant n - x + 1;
    */
    while (x <= n) {
        y = n - x;
        x = x +1;
    }
    if (n > 0) {
      //@ assert y < n;
    }
}