/*@ assigns \nothing; */
extern int unknown(void);

/*@
  requires 0 <= x <= 10;
  requires 0 <= y <= 10;
*/
void foo(int x, int y) {
  /*@
    loop invariant x >= 0;
    loop invariant y >= 0;
    loop invariant y >= x - 10;
    loop assigns x, y;
  */
  while (unknown()) {
    x  = x + 10;
    y  = y + 10;
  }
  if (x == 20) {
    //@ assert y != 0;
  }
}
