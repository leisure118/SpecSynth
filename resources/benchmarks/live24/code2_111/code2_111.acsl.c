/*@
requires 1 <= n;
*/
void foo(int n) {
  int i = 1;
  int sn = 0;
  /*@
    loop invariant 1 <= i <= n+1;
    loop invariant sn == i - 1;
    loop assigns i, sn;
    loop variant n + 1 - i;
  */
  while (i <= n) {
    i = i + 1;
    sn = sn + 1;
  }
  if (sn != 0) {
    //@ assert sn == n;
  }
}