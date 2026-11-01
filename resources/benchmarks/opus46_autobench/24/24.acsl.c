/*@
requires i == 1;
requires j == 10;
*/
void foo(int i, int j) {
  // loop body
  /*@
    loop invariant i + 2*j == 21;
    loop invariant j >= 6;
    loop invariant i >= 1;
    loop assigns i, j;
    loop variant j - 6;
  */
  while (j >= i) {
    i  = i + 2;
    j  = j - 1;
  }
  // post-condition
  //@ assert(j == 6);
}
