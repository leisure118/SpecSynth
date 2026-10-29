/*@
requires n >= 0;
requires k >= 0;
*/
void foo(int k, int n) {
  int i = 0;
  int j = 0;
  
  /*@
    loop invariant 0 <= i <= n+1;
    loop invariant j == i*(i+1)/2;
    loop assigns i, j;
    loop variant n+1 - i;
  */
  while (i <= n) {
    i  = i + 1;
    j  = j + i;
  }
  // post-condition
  //@ assert(i + j + k > 2*n);
}
