/*@ assigns \nothing; */
int unknown(void);

int main() {
  int sn = 0;
  int x = 0;
  /*@
    loop invariant sn == x;
    loop invariant sn >= 0;
    loop assigns x, sn;
  */
  while (unknown()) {
    x = x + 1;
    sn = sn + 1;
  }
  if(sn != x) {
    //@ assert sn == -1;
  }
}
