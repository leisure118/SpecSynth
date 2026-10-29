int main() {
  int sn = 0;
  int x = 0;
  
  /*@
    loop invariant sn == x;
    loop assigns x, sn;
  */
  while (unknown()) {
    x = x + 1;
    sn = sn + 1;
  }
  // post-condition
  if(sn != x) {
    //@ assert(sn == -1);
  }
}
