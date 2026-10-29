/*@
  requires \valid(a) && \valid(b);
  requires \separated(a, b);
  assigns *a;
  ensures *a == \old(*a) + \old(*b);
  ensures \result == *a;
  ensures *b == \old(*b);
*/
int incr_a_by_b(int* a, int const* b){
    *a += *b;
    return *a;
}
void main() {
    int a = 10;
    int b = 20;
    incr_a_by_b(&a, &b);
    //@ assert a == 30;
    //@ assert b == 20;
}
