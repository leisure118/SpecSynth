/*@ assigns \nothing; */
extern int unknown(void);

int main() {
  int sn = 0;
  int x = 0;
  /*@
    loop invariant sn == x;
    loop invariant sn >= 0;
    loop assigns sn, x;
  */
  while (unknown()) {
    x  = x + 1;
    sn  = sn + 1;
  }
  if (sn != -1) {
    //@ assert sn == x;
  }
}
