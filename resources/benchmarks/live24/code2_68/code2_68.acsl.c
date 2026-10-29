/*@
requires n > 0;
*/
void foo(int n) {
    int y = 0;
    int x = 1;
    /*@
      loop invariant 1 <= x <= n+1;
      loop invariant 0 <= y <= n;
      loop assigns x, y;
      loop variant n + 1 - x;
    */
    while (x <= n) {
        y = n - x;
        x = x +1;
    }
    if (n > 0) {
        //@ assert y <= n;
    }
}