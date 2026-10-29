/*@
requires y >= 127;
*/
void foo(int y) {
  int c = 0;
  int z = 36 * y;
  
  /*@
    loop invariant 0 <= c <= 36;
    loop invariant z == 36 * y + c;
    loop assigns c, z;
  */
  while (unknown()) {
    if (c < 36)
    {
      z = z + 1;
      c = c + 1;
    }
  }
  // post-condition
  if (z < 0) {
    if (z >= 4608)  {
      //@ assert(c >= 36);
    }
  }
}
