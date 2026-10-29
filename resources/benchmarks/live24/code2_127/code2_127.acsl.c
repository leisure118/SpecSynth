/*@
  requires x >= 0;
  assigns \nothing;
*/
void foo(int x, int y) {
  int i = x;
  int j = y;
  /*@
    loop invariant x >= 0;
    loop invariant y - x == j - i;
    loop assigns x, y;
    loop variant x;
  */
  while (x != 0) {
    x  = x - 1;
    y  = y - 1;
  }
  if (y != 0) {
    //@ assert i != j;
  }
}