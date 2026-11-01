/*@ assigns \nothing; */
int unknown(void);

/*@
  requires 0 <= x <= 10;
  requires 0 <= y <= 10;
*/
void foo(int x, int y) {
  /*@
    loop invariant -10 <= x - y <= 10;
    loop invariant y >= 0;
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
