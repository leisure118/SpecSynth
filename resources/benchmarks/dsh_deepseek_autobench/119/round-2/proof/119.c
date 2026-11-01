/*@
  requires size >= 1;
  assigns \nothing;
*/
void foo(int size) {
  int i = 1;
  int sn = 0;
  
  /*@
    loop invariant sn == i - 1;
    loop invariant 0 <= sn <= size;
    loop assigns i, sn;
    loop variant size - i;
  */
  while (i <= size) {  
    i = i + 1;
    sn = sn + 1;
  }
  // post-condition
  if (sn != 0) {
    //@ assert(sn == size);
  }
}
