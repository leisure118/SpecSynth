void f(int n, int *p, int *q) {
    if (n > 0) *p = n;
    else *q = n;
}
int main(){
    int n = 10;
    int p = 1,q = 2;
    f(n, &p, &q);
    //@ assert p == 10;
    n = -10;
    f(n, &p, &q);
    //@ assert q == -10;
}