/*@ assigns \nothing; */
int unknown(void);

/*@
  requires 0 <= x <= 2;
  requires 0 <= y <= 2;
*/
void foo(int x, int y) {
  // loop body
  /*@
    loop invariant x >= 0;
    loop invariant y >= 0;
    loop invariant y >= x - 2;
    loop assigns x, y;
  */
  while (unknown()) {
    x  = x + 2;
    y  = y + 2;
  }
  // post-condition
  if (x == 4) {
    //@ assert(y != 0);
  }
}
