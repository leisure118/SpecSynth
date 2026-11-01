/*@ assigns \nothing; */
extern int unknown(void);

/*@
  requires 0 <= x <= 2;
  requires 0 <= y <= 2;
*/
void foo(int x, int y) {
  // loop body
  /*@
    loop invariant y >= 0;
    loop invariant x <= y + 2;
    loop assigns x, y;
  */
  while (unknown()) {
    x  = x + 2;
    y  = y + 2;
  }
  // post-condition
  if (y == 0) {
    //@ assert(x != 4);
  }
}
