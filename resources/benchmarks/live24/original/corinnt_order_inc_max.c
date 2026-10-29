/*@
  requires \valid(a) && \valid(b);
  assigns  *a, *b ;
  behavior reorder:
    assumes *a < *b ;
    ensures *a == \old(*b) && *b == \old(*a) ;
  behavior do_not_change:
    assumes *a >= *b ;
    ensures *a == \old(*a) && *b == \old(*b) ;
  complete behaviors ;
  disjoint behaviors ;
*/
void max_ptr(int* a, int* b){
  if(*a < *b){
    int tmp = *b ;
    *b = *a ;
    *a = tmp ;
  }
  //@ assert *a >= *b ;
}
/*@
  requires \valid(a) && \valid(b);
  assigns  *a, *b ;
  behavior reorder:
    assumes *a > *b ;
    ensures *a == \old(*b) && *b == \old(*a) ;
  behavior do_not_change:
    assumes *a <= *b ;
    ensures *a == \old(*a) && *b == \old(*b) ;
  complete behaviors ;
  disjoint behaviors ;
*/
void min_ptr(int* a, int* b){
  max_ptr(b, a);
  //@ assert *a <= *b ;
}

void order_3_inc_max_min(int* a, int* b, int* c) {
  max_ptr(c, b) ;
  max_ptr(c, a) ;
  max_ptr(b, a) ;
  //@ assert *a <= *b && *b <= *c ;
}
