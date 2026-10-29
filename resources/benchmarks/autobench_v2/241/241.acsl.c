// hhk2008_true-unreach-call.c
int main() {
    int a;
    int b;

    int res, cnt;

    res = a;
    cnt = b;

    /*@
      loop invariant res + cnt == a + b;
      loop assigns cnt, res;
      loop variant cnt;
    */
    while (cnt > 0) {
    	cnt = cnt - 1;
        res = res + 1;
    }

    //@ assert(res == a + b);

    return 0;
}
