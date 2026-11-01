/*@
requires i == 1;
requires j == 20;
*/
void foo(int i, int j) {
  // loop body
  /*@
    loop invariant i + 2*j == 41;
    loop invariant j >= 13;
    loop invariant i >= 1;
    loop assigns i, j;
    loop variant j - i;
  */
  while (j >= i) {
    i  = i + 2;
    j  = j - 1;
  }
  // post-condition
  //@ assert(j == 13);
}
