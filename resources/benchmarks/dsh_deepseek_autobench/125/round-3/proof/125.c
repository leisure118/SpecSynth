/*@
  requires x >= 0;
  requires y - x >= -2147483647;
  assigns \nothing;
*/
void foo(int x, int y) {
  int i = x;
  int j = y;
  
  /*@
    loop invariant x - y == i - j;
    loop invariant x >= 0;
    loop invariant y - x >= -2147483647;
    loop assigns x, y;
    loop variant x;
  */
  while (x != 0) {
    x = x - 1;
    y = y - 1;
  }
  // post-condition
  if(y != 0) {
    //@ assert(i != j);
  }
}
