/*@
requires n > 0;
*/
void foo(int n) {
    int x = 1;
    int y = 0;
    /*@
      loop invariant 1 <= x <= n+1;
      loop invariant y >= 0;
      loop assigns x, y;
      loop variant n + 1 - x;
    */
    while (x <= n) {
        y = n - x;
        x = x +1;
    }
    if (n > 0) {
      //@ assert y >= 0;
    }
}