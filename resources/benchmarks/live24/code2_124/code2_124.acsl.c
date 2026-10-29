/*@
  requires x >= 0;
*/
void foo(int x, int y) {
  int i = x;
  int j = y;
  /*@
    loop invariant x >= 0;
    loop invariant i - x == j - y;
    loop assigns x, y;
    loop variant x;
  */
  while (x != 0) {
    x  = x - 1;
    y  = y - 1;
  }
  if(i == j) {
    //@ assert y == 0;
  }
}