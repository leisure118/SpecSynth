/*@
  requires n > 0;
  assigns \nothing;
*/
void foo(int n) {
  int c = 0;
  /*@
    loop invariant 0 <= c;
    loop assigns c;
  */
  while (unknown()) {
    if (unknown()) {
      if (c > n) {
        c = c + 1;
      }
    } else {
      if (c == n) {
        c = 1;
      }
    }
  }
  if (c != n) {
    //@ assert c >= 0;
  }
}
