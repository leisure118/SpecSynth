#include<limits.h>
/*@
  requires \valid_read(a);
  requires *a + 5 <= INT_MAX;
  assigns \nothing;
  ensures \result == \old(*a) + 5;
*/
int plus_5(int* a) {
    return *a + 5;
}
int main(){
    int a = 10;
    int b = plus_5(&a);
    //@ assert b == 15;
}
