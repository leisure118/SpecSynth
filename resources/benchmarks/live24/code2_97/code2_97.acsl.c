/*@
  requires x >= 0;
  assigns \nothing;
*/
void foo(int x) {
  int i = 0;
  int j = 0;
  int y = 2;
  /*@
    loop invariant 0 <= i <= x+1;
    loop invariant j == 2*i;
    loop invariant y == 2;
    loop assigns i, j;
    loop variant x+1 - i;
  */
  while (i <= x) {
    i  = i + 1;
    j  = j + y;
  }
  if (y == 1) {
    //@ assert i == j;
  }
}
