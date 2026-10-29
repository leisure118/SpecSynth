/*@
  requires y > 0;
  requires \valid(q) && \valid(r);
  requires \separated(q, r);
  assigns *q, *r;
  ensures *q * y + *r == x;
  ensures *r < y;
*/
void div_rem(unsigned x, unsigned y, unsigned* q, unsigned* r){
     unsigned qv = x / y;
     unsigned rv = x % y;
     *q = qv;
     *r = rv;
     //@ assert qv * y + rv == x;
}
int main() {
    unsigned x = 10, y = 3;
    unsigned q, r;
    div_rem(x, y, &q, &r);
    //@ assert q == 3 && r == 1;
    return 0;
}
