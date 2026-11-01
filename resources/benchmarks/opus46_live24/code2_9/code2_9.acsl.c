/*@ assigns \nothing; */
int unknown(void);

/*@
  requires 0 <= x <= 2;
  requires 0 <= y <= 2;
*/
void foo(int x, int y) {
  /*@
    loop invariant y == x - \at(x, Pre) + \at(y, Pre);
    loop assigns x, y;
  */
  while (unknown()) {
    x  = x + 2;
    y  = y + 2;
  }
  if (x == 4) {
    //@ assert y != 0;
  }
}