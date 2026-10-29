#include <stddef.h>
#include <limits.h>
/*@
  requires \valid(a) && \valid(b);
  requires \separated(a, b);
  assigns *a, *b;
  ensures *a >= *b;
  ensures (*a == \old(*a) && *b == \old(*b)) || (*a == \old(*b) && *b == \old(*a));
*/
void max_ptr(int* a, int* b) {
    if(*a < *b) {
      int tmp = *b ;
      *b = *a ;
      *a = tmp;
    }
}
extern int h ;
int main() {
  h = 42 ;
  int a = 24 ;
  int b = 42 ;
  max_ptr(&a, &b) ;
  //@ assert a == 42 ;
  //@ assert b == 24 ;
}
