/*@
requires 1 <= n;
*/
/*@
requires n <= 2147483645;
*/
void foo(int n) {
  int i = 1;
  int sn = 0;
  
  /*@
    loop invariant i == sn + 1;
    loop invariant 1 <= i;
    loop invariant i <= n + 1;
    loop assigns i, sn;
    loop variant n - i + 1;
  */
  while (i <= n) {
    i = i + 1;
    sn = sn + 1;
  }
  // post-condition
  if (sn != 0) {
    //@ assert(sn == n);
  }
}
