// sum01_true-unreach-call_true-termination.c
int main() {
    int n;
    int i=0;
    int sn=0;
    
    /*@
      loop invariant 1 <= i;
      loop invariant (n >= 1 ==> i <= n+1);
      loop invariant (n >= 1 ==> sn == 2*(i-1));
      loop invariant (n < 1 ==> sn == 0 && i == 1);
      loop assigns i, sn;
      loop variant n+1 - i;
    */
    for (i = 1; i <= n; i++) {
        sn = sn + (2);
    }
    
    //@ assert(sn == n * (2) || sn == 0);
    
    return 0;
}
