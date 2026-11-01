/*@
  requires x >= 0;
  requires y - x >= -2147483647;
  assigns \nothing;
*/
void foo(int x, int y) {
  int i = x;
  int j = y;
  
  /*@
  loop invariant y - x == j - i;
  loop invariant x >= 0;
  loop assigns x, y;
  loop variant x;
*/
  while (x != 0) {
    x  = x - 1;
    y  = y - 1;
  }
  
  // post-condition
  if(i == j) {
    //@ assert(y == 0);
  }
}
